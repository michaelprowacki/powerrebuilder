#!/usr/bin/env python3
"""
Generate modern Flutter and Python code from object model.
"""

import json
from pathlib import Path
import sys
from typing import Dict


class FlutterGenerator:
    """Generate Flutter/Dart code from object model."""

    def __init__(self, model_file: Path, output_dir: Path):
        """Initialize Flutter generator.

        Args:
            model_file: Path to flutter_model.json
            output_dir: Output directory for Flutter code
        """
        self.model_file = model_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(model_file, "r") as f:
            self.model = json.load(f)

    def generate(self):
        """Generate all Flutter code."""
        self._generate_main()
        self._generate_screens()
        self._generate_widgets()
        self._generate_models()
        self._generate_pubspec()

    def _generate_main(self):
        """Generate main.dart."""
        code = """import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const DentalClinicApp());
}

class DentalClinicApp extends StatelessWidget {
  const DentalClinicApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dental Clinic Management',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
"""
        output_file = self.output_dir / "lib" / "main.dart"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        print(f"Generated: {output_file}")

    def _generate_screens(self):
        """Generate screen files."""
        screens_dir = self.output_dir / "lib" / "screens"
        screens_dir.mkdir(parents=True, exist_ok=True)

        # Generate home screen with navigation to all screens
        home_code = """import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dental Clinic Management System'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      drawer: _buildDrawer(context),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.medical_services, size: 100, color: Colors.blue),
            const SizedBox(height: 20),
            const Text(
              'Welcome to Dental Clinic System',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 40),
            _buildModuleCard('Patient Management', Icons.person, context),
            _buildModuleCard('Appointments', Icons.calendar_today, context),
            _buildModuleCard('Billing', Icons.payment, context),
          ],
        ),
      ),
    );
  }

  Widget _buildModuleCard(String title, IconData icon, BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(10),
      child: ListTile(
        leading: Icon(icon, size: 40),
        title: Text(title, style: const TextStyle(fontSize: 18)),
        trailing: const Icon(Icons.arrow_forward),
        onTap: () {
          // Navigate to module
        },
      ),
    );
  }

  Widget _buildDrawer(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const DrawerHeader(
            decoration: BoxDecoration(color: Colors.blue),
            child: Text('Menu', style: TextStyle(color: Colors.white, fontSize: 24)),
          ),
          ListTile(
            leading: const Icon(Icons.dashboard),
            title: const Text('Dashboard'),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.person),
            title: const Text('Patients'),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('Settings'),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}
"""
        home_file = screens_dir / "home_screen.dart"
        home_file.write_text(home_code)
        print(f"Generated: {home_file}")

        # Generate screens from model
        for screen in self.model["screens"][:5]:  # First 5 screens
            screen_code = self._generate_screen_code(screen)
            screen_file = screens_dir / f"{screen['name'].lower()}_screen.dart"
            screen_file.write_text(screen_code)
            print(f"Generated: {screen_file}")

    def _generate_screen_code(self, screen: Dict) -> str:
        """Generate code for a single screen."""
        widgets_code = []
        for widget in screen["widgets"][:10]:  # First 10 widgets
            if widget["type"] == "ElevatedButton":
                widgets_code.append(f"""
            ElevatedButton(
              onPressed: () {{}},
              child: const Text('{widget["name"]}'),
            ),""")
            elif widget["type"] == "Text":
                widgets_code.append(f"""
            const Text('{widget["name"]}'),""")
            elif widget["type"] == "TextField":
                widgets_code.append(f"""
            TextField(
              decoration: const InputDecoration(
                labelText: '{widget["name"]}',
              ),
            ),""")

        return f"""import 'package:flutter/material.dart';

class {screen["name"]}Screen extends StatefulWidget {{
  const {screen["name"]}Screen({{super.key}});

  @override
  State<{screen["name"]}Screen> createState() => _{screen["name"]}ScreenState();
}}

class _{screen["name"]}ScreenState extends State<{screen["name"]}Screen> {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{screen["name"]}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            {"".join(widgets_code)}
          ],
        ),
      ),
    );
  }}
}}
"""

    def _generate_widgets(self):
        """Generate custom widget files."""
        widgets_dir = self.output_dir / "lib" / "widgets"
        widgets_dir.mkdir(parents=True, exist_ok=True)

        # Generate a data table widget
        table_code = """import 'package:flutter/material.dart';

class CustomDataTable extends StatelessWidget {
  final List<Map<String, dynamic>> data;
  final List<String> columns;

  const CustomDataTable({
    super.key,
    required this.data,
    required this.columns,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: columns.map((col) => DataColumn(label: Text(col))).toList(),
        rows: data.map((row) {
          return DataRow(
            cells: columns.map((col) {
              return DataCell(Text(row[col]?.toString() ?? ''));
            }).toList(),
          );
        }).toList(),
      ),
    );
  }
}
"""
        table_file = widgets_dir / "custom_data_table.dart"
        table_file.write_text(table_code)
        print(f"Generated: {table_file}")

    def _generate_models(self):
        """Generate data model files."""
        models_dir = self.output_dir / "lib" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Generate patient model
        patient_code = """class Patient {
  final int id;
  final String firstName;
  final String lastName;
  final String email;
  final String phone;
  final DateTime dateOfBirth;
  final String address;

  Patient({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.phone,
    required this.dateOfBirth,
    required this.address,
  });

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'],
      firstName: json['firstName'],
      lastName: json['lastName'],
      email: json['email'],
      phone: json['phone'],
      dateOfBirth: DateTime.parse(json['dateOfBirth']),
      address: json['address'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'firstName': firstName,
      'lastName': lastName,
      'email': email,
      'phone': phone,
      'dateOfBirth': dateOfBirth.toIso8601String(),
      'address': address,
    };
  }
}
"""
        patient_file = models_dir / "patient.dart"
        patient_file.write_text(patient_code)
        print(f"Generated: {patient_file}")

    def _generate_pubspec(self):
        """Generate pubspec.yaml."""
        pubspec = """name: dental_clinic_app
description: Dental Clinic Management System
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
  http: ^1.1.0
  provider: ^6.0.5
  shared_preferences: ^2.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""
        pubspec_file = self.output_dir / "pubspec.yaml"
        pubspec_file.write_text(pubspec)
        print(f"Generated: {pubspec_file}")


class PythonGenerator:
    """Generate Python/Litestar code from object model."""

    def __init__(self, model_file: Path, output_dir: Path):
        """Initialize Python generator.

        Args:
            model_file: Path to python_model.json
            output_dir: Output directory for Python code
        """
        self.model_file = model_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(model_file, "r") as f:
            self.model = json.load(f)

    def generate(self):
        """Generate all Python code."""
        self._generate_main()
        self._generate_models()
        self._generate_services()
        self._generate_api()
        self._generate_requirements()

    def _generate_main(self):
        """Generate main.py."""
        code = '''"""
Dental Clinic Management System API
Generated from PowerBuilder system
"""

from litestar import Litestar
from litestar.config.cors import CORSConfig

from api.patient_api import PatientController
from api.appointment_api import AppointmentController
from api.billing_api import BillingController

cors_config = CORSConfig(
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = Litestar(
    route_handlers=[
        PatientController,
        AppointmentController,
        BillingController,
    ],
    cors_config=cors_config,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        main_file = self.output_dir / "main.py"
        main_file.write_text(code)
        print(f"Generated: {main_file}")

    def _generate_models(self):
        """Generate model files."""
        models_dir = self.output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Generate patient model
        patient_code = '''"""Patient data model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class Patient(BaseModel):
    """Patient entity."""

    id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: datetime
    address: str
    medical_history: Optional[str] = None
    insurance_info: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        orm_mode = True
'''
        patient_file = models_dir / "patient.py"
        patient_file.write_text(patient_code)
        print(f"Generated: {patient_file}")

        # Generate appointment model
        appointment_code = '''"""Appointment data model."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Appointment(BaseModel):
    """Appointment entity."""

    id: Optional[int] = None
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    reason: str
    notes: Optional[str] = None
    status: str = "scheduled"  # scheduled, confirmed, completed, cancelled
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
'''
        appointment_file = models_dir / "appointment.py"
        appointment_file.write_text(appointment_code)
        print(f"Generated: {appointment_file}")

    def _generate_services(self):
        """Generate service files."""
        services_dir = self.output_dir / "services"
        services_dir.mkdir(parents=True, exist_ok=True)

        # Generate patient service
        patient_service_code = '''"""Patient service layer."""

from typing import List, Optional
from models.patient import Patient

class PatientService:
    """Service for patient operations."""

    def __init__(self):
        # In real app, inject repository
        self.patients: List[Patient] = []
        self._next_id = 1

    async def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return self.patients

    async def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        return next((p for p in self.patients if p.id == patient_id), None)

    async def create_patient(self, patient: Patient) -> Patient:
        """Create new patient."""
        patient.id = self._next_id
        self._next_id += 1
        self.patients.append(patient)
        return patient

    async def update_patient(self, patient_id: int, patient_data: Patient) -> Optional[Patient]:
        """Update patient."""
        patient = await self.get_patient_by_id(patient_id)
        if patient:
            # Update fields
            for key, value in patient_data.dict(exclude_unset=True).items():
                setattr(patient, key, value)
        return patient

    async def delete_patient(self, patient_id: int) -> bool:
        """Delete patient."""
        patient = await self.get_patient_by_id(patient_id)
        if patient:
            self.patients.remove(patient)
            return True
        return False
'''
        patient_service_file = services_dir / "patient_service.py"
        patient_service_file.write_text(patient_service_code)
        print(f"Generated: {patient_service_file}")

    def _generate_api(self):
        """Generate API controller files."""
        api_dir = self.output_dir / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        # Generate patient API
        patient_api_code = '''"""Patient API endpoints."""

from typing import List
from litestar import Controller, get, post, put, delete
from litestar.di import Provide

from models.patient import Patient
from services.patient_service import PatientService

def provide_patient_service() -> PatientService:
    """Provide patient service instance."""
    return PatientService()

class PatientController(Controller):
    """Patient API controller."""

    path = "/api/patients"
    dependencies = {"service": Provide(provide_patient_service)}

    @get()
    async def list_patients(self, service: PatientService) -> List[Patient]:
        """Get all patients."""
        return await service.get_all_patients()

    @get("/{patient_id:int}")
    async def get_patient(self, patient_id: int, service: PatientService) -> Patient:
        """Get patient by ID."""
        patient = await service.get_patient_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        return patient

    @post()
    async def create_patient(self, data: Patient, service: PatientService) -> Patient:
        """Create new patient."""
        return await service.create_patient(data)

    @put("/{patient_id:int}")
    async def update_patient(
        self, patient_id: int, data: Patient, service: PatientService
    ) -> Patient:
        """Update patient."""
        patient = await service.update_patient(patient_id, data)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        return patient

    @delete("/{patient_id:int}")
    async def delete_patient(self, patient_id: int, service: PatientService) -> dict:
        """Delete patient."""
        success = await service.delete_patient(patient_id)
        if not success:
            raise ValueError(f"Patient {patient_id} not found")
        return {"message": f"Patient {patient_id} deleted"}
'''
        patient_api_file = api_dir / "patient_api.py"
        patient_api_file.write_text(patient_api_code)
        print(f"Generated: {patient_api_file}")

        # Generate stub files for other APIs
        for api_name in ["appointment_api", "billing_api"]:
            stub_code = f'''"""Stub for {api_name}."""

from litestar import Controller

class {api_name.replace("_api", "").capitalize()}Controller(Controller):
    """Controller stub."""
    path = f"/api/{api_name.replace("_api", "")}"

    # TODO: Implement endpoints
'''
            stub_file = api_dir / f"{api_name}.py"
            stub_file.write_text(stub_code)
            print(f"Generated: {stub_file}")

    def _generate_requirements(self):
        """Generate requirements.txt."""
        requirements = """litestar==2.0.0
uvicorn==0.23.0
pydantic==2.0.0
python-dotenv==1.0.0
sqlalchemy==2.0.0
alembic==1.11.0
"""
        req_file = self.output_dir / "requirements.txt"
        req_file.write_text(requirements)
        print(f"Generated: {req_file}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: generate_modern_code.py <model_dir> [output_dir]")
        sys.exit(1)

    model_dir = Path(sys.argv[1])
    output_dir = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/generated_code")
    )

    # Generate Flutter code
    flutter_model = model_dir / "flutter_model.json"
    if flutter_model.exists():
        flutter_output = output_dir / "flutter_app"
        flutter_gen = FlutterGenerator(flutter_model, flutter_output)
        print("\n" + "=" * 60)
        print("Generating Flutter Application")
        print("=" * 60)
        flutter_gen.generate()

    # Generate Python code
    python_model = model_dir / "python_model.json"
    if python_model.exists():
        python_output = output_dir / "python_api"
        python_gen = PythonGenerator(python_model, python_output)
        print("\n" + "=" * 60)
        print("Generating Python/Litestar API")
        print("=" * 60)
        python_gen.generate()

    print("\n" + "=" * 60)
    print("Code Generation Complete!")
    print("=" * 60)
    print("\nTo run the Flutter app:")
    print(f"  cd {output_dir}/flutter_app")
    print("  flutter run")
    print("\nTo run the Python API:")
    print(f"  cd {output_dir}/python_api")
    print("  pip install -r requirements.txt")
    print("  python main.py")


if __name__ == "__main__":
    main()
