"""Comprehensive tests for PowerBuilder transaction handling.

This file consolidates transaction-related tests from:
- test_transaction.py
- test_transaction_error_handling.py
- test_distributed_transaction.py
"""

from datetime import datetime

import pytest

from src.model.distributed_transaction import (
    TransactionPhase,
)
from src.model.transaction import (
    # Distributed transactions
    PBDistributedTransaction,
    PBDistributedTransactionState,
    PBErrorAction,
    PBErrorSeverity,
    # Savepoints
    PBSavepoint,
    PBSavepointManager,
    PBStatementType,
    # Core transaction classes
    PBTransaction,
    PBTransactionCoordinator,
    # Error handling
    PBTransactionError,
    PBTransactionErrorHandler,
    PBTransactionErrorLog,
    PBTransactionObject,
    PBTransactionParticipant,
    PBTransactionState,
    PBTransactionStatement,
    PBTwoPhaseCommit,
    SQLError,
    # SQL execution
    SQLExecutor,
    SQLResult,
)
from src.parse.parser.specialized.transactions import TransactionParser


class TestTransactionObjects:
    """Test transaction object creation and management."""

    def test_transaction_object_creation(self):
        """Test creating transaction objects."""
        txn_obj = PBTransactionObject(
            name="sqlca",
            dbms="ODBC",
            database="MyDB",
            userid="user1",
            dbpass="pass1",
            logid="log1",
            logpass="logpass1",
            servername="server1",
            autocommit=False,
            dbparm="ConnectString='DSN=MyDSN'",
        )

        assert txn_obj.name == "sqlca"
        assert txn_obj.dbms == "ODBC"
        assert txn_obj.database == "MyDB"
        assert txn_obj.userid == "user1"
        assert txn_obj.autocommit is False

    def test_transaction_object_defaults(self):
        """Test transaction object default values."""
        txn_obj = PBTransactionObject(name="sqlca")

        assert txn_obj.name == "sqlca"
        assert txn_obj.dbms == ""
        assert txn_obj.database == ""
        assert txn_obj.userid == ""
        assert txn_obj.dbpass == ""
        assert txn_obj.autocommit is True
        assert txn_obj.sqlcode == 0
        assert txn_obj.sqlerrtext == ""

    def test_multiple_transaction_objects(self):
        """Test managing multiple transaction objects."""
        sqlca = PBTransactionObject(name="sqlca", dbms="ODBC")
        sqlsa = PBTransactionObject(name="sqlsa", dbms="Oracle")
        sqlda = PBTransactionObject(name="sqlda", dbms="Sybase")

        assert sqlca.name != sqlsa.name
        assert sqlsa.dbms != sqlda.dbms
        assert all(obj.sqlcode == 0 for obj in [sqlca, sqlsa, sqlda])

    def test_transaction_object_state(self):
        """Test transaction object state management."""
        txn_obj = PBTransactionObject(name="sqlca")

        # Initial state
        assert txn_obj.sqlcode == 0
        assert txn_obj.sqlerrtext == ""
        assert txn_obj.sqlnrows == 0

        # Simulate successful operation
        txn_obj.sqlcode = 0
        txn_obj.sqlnrows = 5
        assert txn_obj.sqlcode == 0
        assert txn_obj.sqlnrows == 5

        # Simulate error
        txn_obj.sqlcode = -1
        txn_obj.sqlerrtext = "Connection failed"
        assert txn_obj.sqlcode == -1
        assert txn_obj.sqlerrtext == "Connection failed"


class TestTransactionStatements:
    """Test transaction statement execution."""

    def test_transaction_statement_types(self):
        """Test different transaction statement types."""
        # CONNECT
        connect = PBTransactionStatement(
            statement_type=PBStatementType.CONNECT,
            transaction_object="sqlca",
        )
        assert connect.statement_type == PBStatementType.CONNECT

        # DISCONNECT
        disconnect = PBTransactionStatement(
            statement_type=PBStatementType.DISCONNECT,
            transaction_object="sqlca",
        )
        assert disconnect.statement_type == PBStatementType.DISCONNECT

        # COMMIT
        commit = PBTransactionStatement(
            statement_type=PBStatementType.COMMIT,
            transaction_object="sqlca",
        )
        assert commit.statement_type == PBStatementType.COMMIT

        # ROLLBACK
        rollback = PBTransactionStatement(
            statement_type=PBStatementType.ROLLBACK,
            transaction_object="sqlca",
        )
        assert rollback.statement_type == PBStatementType.ROLLBACK

    def test_transaction_with_using_clause(self):
        """Test transaction statements with USING clause."""
        stmt = PBTransactionStatement(
            statement_type="COMMIT",
            transaction_object="my_trans",
            using_clause=True,
        )
        assert stmt.transaction_object == "my_trans"
        assert stmt.using_clause is True

    def test_transaction_statement_validation(self):
        """Test transaction statement validation."""
        # Valid statement
        valid_stmt = PBTransactionStatement(
            statement_type=PBStatementType.CONNECT,
            transaction_object="sqlca",
        )
        assert valid_stmt.is_valid()

        # Invalid statement (no transaction object)
        invalid_stmt = PBTransactionStatement(
            statement_type=PBStatementType.COMMIT,
            transaction_object="",
        )
        assert not invalid_stmt.is_valid()


class TestTransactionLifecycle:
    """Test complete transaction lifecycle."""

    def test_basic_transaction_flow(self):
        """Test basic transaction flow."""
        txn = PBTransaction(name="test_transaction")
        txn_obj = PBTransactionObject(name="sqlca", dbms="ODBC")

        # Connect
        txn.begin(txn_obj)
        assert txn.state == PBTransactionState.ACTIVE
        assert txn.transaction_object == txn_obj

        # Execute operations (simulated)
        txn.execute_statement("INSERT INTO test VALUES (1, 'test')")
        assert len(txn.statements) == 1

        # Commit
        txn.commit()
        assert txn.state == PBTransactionState.COMMITTED
        assert txn.end_time is not None

    def test_transaction_rollback(self):
        """Test transaction rollback."""
        txn = PBTransaction(name="rollback_test")
        txn_obj = PBTransactionObject(name="sqlca")

        # Begin transaction
        txn.begin(txn_obj)
        assert txn.state == PBTransactionState.ACTIVE

        # Execute operations
        txn.execute_statement("UPDATE test SET value = 'new'")
        txn.execute_statement("DELETE FROM test WHERE id = 1")
        assert len(txn.statements) == 2

        # Rollback
        txn.rollback()
        assert txn.state == PBTransactionState.ROLLED_BACK
        assert txn.end_time is not None

    def test_nested_transactions(self):
        """Test nested transaction handling."""
        outer_txn = PBTransaction(name="outer")
        inner_txn = PBTransaction(name="inner", parent=outer_txn)

        txn_obj = PBTransactionObject(name="sqlca")

        # Begin outer transaction
        outer_txn.begin(txn_obj)
        assert outer_txn.state == PBTransactionState.ACTIVE

        # Begin inner transaction
        inner_txn.begin(txn_obj)
        assert inner_txn.state == PBTransactionState.ACTIVE
        assert inner_txn.parent == outer_txn

        # Commit inner
        inner_txn.commit()
        assert inner_txn.state == PBTransactionState.COMMITTED

        # Commit outer
        outer_txn.commit()
        assert outer_txn.state == PBTransactionState.COMMITTED


class TestTransactionErrorHandling:
    """Test transaction error handling."""

    def test_transaction_error_creation(self):
        """Test creating transaction errors."""
        error = PBTransactionError(
            code=-1,
            message="Connection failed",
            severity=PBErrorSeverity.FATAL,
            source="CONNECT",
            timestamp=datetime.now(),
        )

        assert error.code == -1
        assert error.message == "Connection failed"
        assert error.severity == PBErrorSeverity.FATAL
        assert error.source == "CONNECT"

    def test_error_severity_levels(self):
        """Test different error severity levels."""
        info = PBTransactionError(
            code=100,
            message="Info message",
            severity=PBErrorSeverity.INFO,
        )
        assert info.severity == PBErrorSeverity.INFO

        warning = PBTransactionError(
            code=200,
            message="Warning message",
            severity=PBErrorSeverity.WARNING,
        )
        assert warning.severity == PBErrorSeverity.WARNING

        error = PBTransactionError(
            code=-1,
            message="Error message",
            severity=PBErrorSeverity.ERROR,
        )
        assert error.severity == PBErrorSeverity.ERROR

        fatal = PBTransactionError(
            code=-999,
            message="Fatal error",
            severity=PBErrorSeverity.FATAL,
        )
        assert fatal.severity == PBErrorSeverity.FATAL

    def test_error_handler(self):
        """Test transaction error handler."""
        handler = PBTransactionErrorHandler()

        # Register error actions
        handler.register_action(
            error_code=-1,
            action=PBErrorAction.ROLLBACK,
        )
        handler.register_action(
            error_code=-2,
            action=PBErrorAction.RETRY,
            max_retries=3,
        )
        handler.register_action(
            error_code=100,
            action=PBErrorAction.IGNORE,
        )

        # Handle errors
        error1 = PBTransactionError(code=-1, message="Connection lost")
        action1 = handler.handle_error(error1)
        assert action1 == PBErrorAction.ROLLBACK

        error2 = PBTransactionError(code=-2, message="Deadlock")
        action2 = handler.handle_error(error2)
        assert action2 == PBErrorAction.RETRY

        error3 = PBTransactionError(code=100, message="Info")
        action3 = handler.handle_error(error3)
        assert action3 == PBErrorAction.IGNORE

    def test_error_logging(self):
        """Test transaction error logging."""
        log = PBTransactionErrorLog()

        # Log errors
        error1 = PBTransactionError(
            code=-1,
            message="Connection failed",
            timestamp=datetime.now(),
        )
        log.log_error(error1)

        error2 = PBTransactionError(
            code=-2,
            message="Timeout",
            timestamp=datetime.now(),
        )
        log.log_error(error2)

        # Check log
        assert len(log.errors) == 2
        assert log.get_error_count() == 2
        assert log.get_errors_by_code(-1)[0].message == "Connection failed"

        # Clear log
        log.clear()
        assert len(log.errors) == 0


class TestDistributedTransactions:
    """Test distributed transaction handling."""

    def test_distributed_transaction_creation(self):
        """Test creating distributed transactions."""
        dt = PBDistributedTransaction(
            transaction_id="DT001",
            coordinator_node="NODE1",
            participant_nodes=["NODE2", "NODE3", "NODE4"],
        )

        assert dt.transaction_id == "DT001"
        assert dt.coordinator_node == "NODE1"
        assert len(dt.participant_nodes) == 3
        assert dt.state == PBDistributedTransactionState.INITIAL

    def test_two_phase_commit(self):
        """Test two-phase commit protocol."""
        tpc = PBTwoPhaseCommit(transaction_id="TPC001")

        # Add participants
        tpc.add_participant("NODE1")
        tpc.add_participant("NODE2")
        tpc.add_participant("NODE3")

        assert len(tpc.participants) == 3
        assert tpc.phase == TransactionPhase.INITIAL

        # Phase 1: Prepare
        tpc.start_prepare_phase()
        assert tpc.phase == TransactionPhase.PREPARING

        # Participants vote
        tpc.record_vote("NODE1", True)
        tpc.record_vote("NODE2", True)
        tpc.record_vote("NODE3", True)

        # Check if all prepared
        assert tpc.all_prepared()

        # Phase 2: Commit
        tpc.start_commit_phase()
        assert tpc.phase == TransactionPhase.COMMITTING

        # Participants acknowledge
        tpc.record_commit_ack("NODE1")
        tpc.record_commit_ack("NODE2")
        tpc.record_commit_ack("NODE3")

        # Complete
        assert tpc.is_complete()

    def test_distributed_transaction_rollback(self):
        """Test distributed transaction rollback."""
        dt = PBDistributedTransaction(
            transaction_id="DT002",
            coordinator_node="COORD",
            participant_nodes=["P1", "P2", "P3"],
        )

        # Start transaction
        dt.start()
        assert dt.state == PBDistributedTransactionState.ACTIVE

        # Simulate failure on one node
        dt.record_node_failure("P2", "Network error")

        # Rollback
        dt.rollback()
        assert dt.state == PBDistributedTransactionState.ROLLED_BACK
        assert "P2" in dt.failed_nodes

    def test_transaction_coordinator(self):
        """Test transaction coordinator functionality."""
        coordinator = PBTransactionCoordinator(node_id="COORD1")

        # Create distributed transaction
        dt = coordinator.create_distributed_transaction(
            participants=["NODE1", "NODE2"],
        )

        assert dt.coordinator_node == "COORD1"
        assert len(dt.participant_nodes) == 2

        # Execute transaction
        result = coordinator.execute_transaction(dt)
        assert result.transaction_id == dt.transaction_id

    def test_transaction_participant(self):
        """Test transaction participant functionality."""
        participant = PBTransactionParticipant(
            node_id="PART1",
            resource_manager="DB1",
        )

        assert participant.node_id == "PART1"
        assert participant.resource_manager == "DB1"

        # Prepare phase
        prepared = participant.prepare(transaction_id="TXN001")
        assert isinstance(prepared, bool)

        # Commit phase
        if prepared:
            committed = participant.commit(transaction_id="TXN001")
            assert isinstance(committed, bool)


class TestSavepoints:
    """Test savepoint functionality."""

    def test_savepoint_creation(self):
        """Test creating savepoints."""
        sp = PBSavepoint(
            name="SP1",
            transaction_id="TXN001",
            sequence_number=1,
        )

        assert sp.name == "SP1"
        assert sp.transaction_id == "TXN001"
        assert sp.sequence_number == 1
        assert sp.created_at is not None

    def test_savepoint_manager(self):
        """Test savepoint manager."""
        manager = PBSavepointManager(transaction_id="TXN001")

        # Create savepoints
        sp1 = manager.create_savepoint("SP1")
        sp2 = manager.create_savepoint("SP2")
        sp3 = manager.create_savepoint("SP3")

        assert len(manager.savepoints) == 3
        assert sp1.sequence_number < sp2.sequence_number
        assert sp2.sequence_number < sp3.sequence_number

        # Rollback to savepoint
        manager.rollback_to_savepoint("SP2")
        assert len(manager.savepoints) == 2
        assert manager.get_savepoint("SP3") is None

        # Release savepoint
        manager.release_savepoint("SP1")
        assert len(manager.savepoints) == 1
        assert manager.get_savepoint("SP1") is None

    def test_nested_savepoints(self):
        """Test nested savepoint handling."""
        manager = PBSavepointManager(transaction_id="TXN002")

        # Create nested savepoints
        sp_outer = manager.create_savepoint("OUTER")
        sp_inner1 = manager.create_savepoint("INNER1")
        sp_inner2 = manager.create_savepoint("INNER2")

        # Verify nesting
        assert sp_outer.sequence_number < sp_inner1.sequence_number
        assert sp_inner1.sequence_number < sp_inner2.sequence_number

        # Rollback to outer savepoint
        manager.rollback_to_savepoint("OUTER")
        assert len(manager.savepoints) == 1
        assert manager.get_savepoint("INNER1") is None
        assert manager.get_savepoint("INNER2") is None


class TestSQLExecution:
    """Test SQL execution within transactions."""

    def test_sql_executor(self):
        """Test SQL executor functionality."""
        executor = SQLExecutor(transaction_object="sqlca")

        # Execute SELECT
        result = executor.execute_select(
            sql="SELECT * FROM employee WHERE dept_id = :dept",
            parameters={":dept": 100},
        )
        assert isinstance(result, SQLResult)

        # Execute INSERT
        result = executor.execute_insert(
            sql="INSERT INTO employee (id, name) VALUES (:id, :name)",
            parameters={":id": 1, ":name": "John"},
        )
        assert isinstance(result, SQLResult)

        # Execute UPDATE
        result = executor.execute_update(
            sql="UPDATE employee SET salary = :sal WHERE id = :id",
            parameters={":sal": 50000, ":id": 1},
        )
        assert isinstance(result, SQLResult)

    def test_sql_result(self):
        """Test SQL result handling."""
        # Successful result
        success_result = SQLResult(
            success=True,
            rows_affected=5,
            data=[
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"},
            ],
            message="Query executed successfully",
        )
        assert success_result.success is True
        assert success_result.rows_affected == 5
        assert len(success_result.data) == 2

        # Error result
        error_result = SQLResult(
            success=False,
            error=SQLError(
                code=-1,
                message="Table not found",
                sql_state="42S02",
            ),
            message="Query failed",
        )
        assert error_result.success is False
        assert error_result.error.code == -1
        assert error_result.error.sql_state == "42S02"

    def test_sql_error_handling(self):
        """Test SQL error handling."""
        error = SQLError(
            code=-206,
            message="Column not found",
            sql_state="42S22",
            source_sql="SELECT invalid_col FROM table",
        )

        assert error.code == -206
        assert error.message == "Column not found"
        assert error.sql_state == "42S22"
        assert "invalid_col" in error.source_sql


class TestTransactionParser:
    """Test transaction parsing functionality."""

    def test_parse_connect_statement(self):
        """Test parsing CONNECT statement."""
        parser = TransactionParser()

        # Simple CONNECT
        result = parser.parse("CONNECT;")
        assert result.statement_type == PBStatementType.CONNECT
        assert result.transaction_object == "sqlca"  # default

        # CONNECT USING
        result = parser.parse("CONNECT USING my_trans;")
        assert result.statement_type == PBStatementType.CONNECT
        assert result.transaction_object == "my_trans"

    def test_parse_disconnect_statement(self):
        """Test parsing DISCONNECT statement."""
        parser = TransactionParser()

        # Simple DISCONNECT
        result = parser.parse("DISCONNECT;")
        assert result.statement_type == PBStatementType.DISCONNECT

        # DISCONNECT USING
        result = parser.parse("DISCONNECT USING sqlsa;")
        assert result.transaction_object == "sqlsa"

    def test_parse_commit_rollback(self):
        """Test parsing COMMIT and ROLLBACK statements."""
        parser = TransactionParser()

        # COMMIT
        result = parser.parse("COMMIT;")
        assert result.statement_type == PBStatementType.COMMIT

        # COMMIT USING
        result = parser.parse("COMMIT USING my_trans;")
        assert result.transaction_object == "my_trans"

        # ROLLBACK
        result = parser.parse("ROLLBACK;")
        assert result.statement_type == PBStatementType.ROLLBACK

        # ROLLBACK USING
        result = parser.parse("ROLLBACK USING sqlca;")
        assert result.transaction_object == "sqlca"

    def test_parse_transaction_properties(self):
        """Test parsing transaction object property assignments."""
        parser = TransactionParser()

        # Parse property assignments
        code = """
        sqlca.dbms = "ODBC"
        sqlca.database = "MyDB"
        sqlca.userid = "user1"
        sqlca.autocommit = false
        """

        txn_obj = parser.parse_transaction_object(code)
        assert txn_obj.dbms == "ODBC"
        assert txn_obj.database == "MyDB"
        assert txn_obj.userid == "user1"
        assert txn_obj.autocommit is False


# Test fixtures
@pytest.fixture
def sample_transaction_object():
    """Provide a sample transaction object."""
    return PBTransactionObject(
        name="sqlca",
        dbms="ODBC",
        database="TestDB",
        userid="testuser",
        dbpass="testpass",
        autocommit=False,
    )


@pytest.fixture
def sample_transaction():
    """Provide a sample transaction."""
    txn = PBTransaction(name="test_txn")
    txn_obj = PBTransactionObject(name="sqlca")
    txn.begin(txn_obj)
    return txn


@pytest.fixture
def sample_distributed_transaction():
    """Provide a sample distributed transaction."""
    return PBDistributedTransaction(
        transaction_id="DT_TEST",
        coordinator_node="COORD",
        participant_nodes=["NODE1", "NODE2", "NODE3"],
    )


@pytest.fixture
def sample_error_handler():
    """Provide a sample error handler."""
    handler = PBTransactionErrorHandler()
    handler.register_action(-1, PBErrorAction.ROLLBACK)
    handler.register_action(-2, PBErrorAction.RETRY, max_retries=3)
    handler.register_action(100, PBErrorAction.IGNORE)
    return handler
