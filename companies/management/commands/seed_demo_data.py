from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import BusinessCard, DigitalCard
from companies.models import Company
from jobcards.models import Specialty, WhiteCardJob
from jobcards.services import ensure_default_specialties
from memberships.models import CompanyMember
from websitebuilder.services import create_starter_website


COMPANIES = [
    {
        "name": "BlueNova Technologies",
        "category": "Tecnologia",
        "city": "Santo Domingo",
        "region": "Distrito Nacional",
        "services": "Desarrollo web, Aplicaciones moviles, Automatizacion, Soporte cloud",
        "description": "Empresa dedicada a crear plataformas digitales, automatizaciones y experiencias web para negocios en crecimiento.",
        "domain": "https://bluenova.example.com",
        "team": [
            ("Adrian Soto", "CEO"),
            ("Marta Reyes", "Product Manager"),
            ("Joel Cabrera", "Frontend Developer"),
            ("Camila Rivas", "UX Designer"),
            ("Nestor Diaz", "Cloud Engineer"),
        ],
    },
    {
        "name": "VitalCare Clinic",
        "category": "Salud",
        "city": "Paterson",
        "region": "New Jersey",
        "services": "Consultas medicas, Enfermeria, Telemedicina, Bienestar preventivo",
        "description": "Clinica moderna orientada a servicios preventivos, atencion primaria y seguimiento personalizado de pacientes.",
        "domain": "https://vitalcare.example.com",
        "team": [
            ("Laura Medina", "Directora Medica"),
            ("Oscar Leon", "Medico General"),
            ("Ruth Alvarez", "Enfermera Jefe"),
            ("Daniela Cruz", "Coordinadora de Pacientes"),
            ("Henry Vargas", "Especialista Telemedicina"),
        ],
    },
    {
        "name": "MetroBuild Contractors",
        "category": "Construccion",
        "city": "Middletown",
        "region": "New York",
        "services": "Remodelacion, Construccion residencial, Plomeria, Electricidad",
        "description": "Contratistas especializados en remodelaciones residenciales, mantenimiento tecnico y soluciones de construccion.",
        "domain": "https://metrobuild.example.com",
        "team": [
            ("Eduar Martinez", "Gerente de Obra"),
            ("Sofia Ortega", "Arquitecta"),
            ("Ivan Molina", "Supervisor Electrico"),
            ("Pedro Santos", "Plomero Senior"),
            ("Ana Paredes", "Coordinadora de Proyectos"),
        ],
    },
    {
        "name": "Sabor Caribe Catering",
        "category": "Gastronomia",
        "city": "Miami",
        "region": "Florida",
        "services": "Catering empresarial, Eventos privados, Cocina caribena, Menu corporativo",
        "description": "Servicio de catering con cocina caribena moderna para empresas, eventos sociales y celebraciones privadas.",
        "domain": "https://saborcaribe.example.com",
        "team": [
            ("Marcos Jimenez", "Chef Ejecutivo"),
            ("Patricia Luna", "Event Manager"),
            ("Rafael Nunez", "Sous Chef"),
            ("Kiara Lopez", "Coordinadora Comercial"),
            ("Tomas Vega", "Logistica"),
        ],
    },
    {
        "name": "BrightPath Learning",
        "category": "Educacion",
        "city": "Orlando",
        "region": "Florida",
        "services": "Tutoria, Cursos online, Capacitacion empresarial, Ingles profesional",
        "description": "Centro educativo enfocado en tutoria personalizada, aprendizaje online y capacitacion para equipos profesionales.",
        "domain": "https://brightpath.example.com",
        "team": [
            ("Elena Suarez", "Directora Academica"),
            ("Miguel Batista", "Instructor STEM"),
            ("Carolina Perez", "Tutora de Ingles"),
            ("Ramon Castillo", "Learning Designer"),
            ("Julia Herrera", "Coordinadora de Cursos"),
        ],
    },
]

JOBS = [
    ("Nadia Gomez", "Diseno Grafico", "Creatividad", "Disenadora grafica con enfoque en identidad visual, contenido social y piezas comerciales para pequenas empresas."),
    ("Luis Herrera", "Desarrollo de Software", "Tecnologia", "Desarrollador full stack con experiencia creando dashboards, APIs REST y automatizaciones."),
    ("Paola Sanchez", "Atencion al Cliente", "Comercial", "Especialista en servicio al cliente, seguimiento de casos y retencion de usuarios."),
    ("Roberto Vega", "Electricidad", "Servicios", "Tecnico electrico residencial y comercial con experiencia en mantenimiento preventivo."),
    ("Diana Morales", "Enfermeria", "Salud", "Enfermera con experiencia en atencion primaria, signos vitales y apoyo a telemedicina."),
    ("Kevin Rojas", "Marketing", "Comercial", "Especialista en marketing digital, campanas locales y contenido para negocios."),
    ("Alba Torres", "Contabilidad", "Administracion", "Asistente contable con dominio de conciliaciones, facturacion y reportes mensuales."),
    ("Felix Navarro", "Mecanica", "Servicios", "Mecanico automotriz con experiencia en diagnostico, mantenimiento y reparacion general."),
    ("Carmen Brito", "Cocina", "Hospitalidad", "Cocinera profesional especializada en preparacion para eventos y menus corporativos."),
    ("Omar Pineda", "Ventas", "Comercial", "Representante comercial orientado a prospeccion, seguimiento y cierre de oportunidades."),
]


class Command(BaseCommand):
    help = "Create demo companies, employee cards, websites and White Card Job candidates."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        ensure_default_specialties()

        company_total = 0
        profile_total = 0
        business_card_total = 0
        website_total = 0

        for index, item in enumerate(COMPANIES, start=1):
            owner = self.get_user(User, f"demo_owner_{index}", item["team"][0][0], f"owner{index}@cardbook.demo")
            company, created = Company.objects.update_or_create(
                name=item["name"],
                defaults={
                    "owner": owner,
                    "address": f"{item['city']}, {item['region']}",
                    "phone_number": f"+1 555 20{index:02d} 0100",
                    "email": f"contacto{index}@cardbook.demo",
                    "website": item["domain"],
                    "description": item["description"],
                    "category": item["category"],
                    "services": item["services"],
                    "city": item["city"],
                    "region": item["region"],
                    "is_active": True,
                },
            )
            company_total += 1
            CompanyMember.objects.get_or_create(company=company, user=owner, defaults={"role": CompanyMember.ROLE_OWNER})

            website = create_starter_website(company, title=item["name"], publish=True)
            website.is_published = True
            website.save(update_fields=["is_published", "updated_at"])
            website_total += 1

            for employee_index, (full_name, job_title) in enumerate(item["team"], start=1):
                user = self.get_user(
                    User,
                    f"demo_emp_{index}_{employee_index}",
                    full_name,
                    f"employee{index}{employee_index}@cardbook.demo",
                )
                CompanyMember.objects.get_or_create(company=company, user=user, defaults={"role": CompanyMember.ROLE_STAFF})
                profile, _ = DigitalCard.objects.get_or_create(
                    company=company,
                    user=user,
                    defaults={
                        "job_title": job_title,
                        "phone_number": f"+1 555 30{index}{employee_index} 0100",
                        "email": user.email,
                        "website": item["domain"],
                        "linkedin_url": f"https://linkedin.com/in/{user.username}",
                        "qr_shape": DigitalCard.QR_SHAPE_DIAMOND,
                        "is_active": True,
                    },
                )
                profile.job_title = job_title
                profile.phone_number = f"+1 555 30{index}{employee_index} 0100"
                profile.email = user.email
                profile.website = item["domain"]
                profile.linkedin_url = f"https://linkedin.com/in/{user.username}"
                profile.is_active = True
                profile.save()
                profile_total += 1

                business_card, _ = BusinessCard.objects.get_or_create(
                    profile=profile,
                    display_name=full_name,
                    defaults={
                        "job_title": job_title,
                        "company_name": company.name,
                        "phone_number": profile.phone_number,
                        "email": profile.email,
                        "website": profile.website,
                        "address": company.address,
                        "tagline": "Conecta. Comparte. Crece.",
                        "services": item["services"],
                        "background_color": "#003875",
                        "accent_color": "#d8a441",
                        "text_color": "#ffffff",
                        "include_qr": True,
                        "is_active": True,
                    },
                )
                business_card.job_title = job_title
                business_card.company_name = company.name
                business_card.phone_number = profile.phone_number
                business_card.email = profile.email
                business_card.website = profile.website
                business_card.address = company.address
                business_card.services = item["services"]
                business_card.is_active = True
                business_card.save()
                business_card_total += 1

        job_total = 0
        for index, (full_name, specialty_name, category, description) in enumerate(JOBS, start=1):
            user = self.get_user(User, f"demo_job_{index}", full_name, f"job{index}@cardbook.demo")
            specialty, _ = Specialty.objects.get_or_create(
                name=specialty_name,
                defaults={"category": category, "description": f"Perfil laboral de {specialty_name}."},
            )
            if not specialty.category:
                specialty.category = category
                specialty.save(update_fields=["category"])
            card, _ = WhiteCardJob.objects.get_or_create(
                user=user,
                is_active=True,
                defaults={
                    "title": "Busco Trabajo",
                    "phone_number": f"+1 555 90{index:02d} 0100",
                    "address": ["Santo Domingo, RD", "Paterson, NJ", "Middletown, NY", "Miami, FL", "Orlando, FL"][index % 5],
                    "linkedin_url": f"https://linkedin.com/in/{user.username}",
                    "resume_url": f"https://drive.google.com/demo-resume-{index}",
                    "specialty": specialty,
                    "short_description": description,
                    "experience": f"{2 + index % 5}+ anos",
                    "languages": "Espanol, Ingles basico",
                    "technologies": "Herramientas digitales, comunicacion profesional",
                    "certifications": "Certificacion disponible bajo solicitud",
                    "availability_note": "Tiempo completo",
                    "quote": "Trabajo con responsabilidad, puntualidad y enfoque en resultados.",
                    "is_available": True,
                },
            )
            card.specialty = specialty
            card.short_description = description
            card.is_active = True
            card.is_available = True
            card.save()
            job_total += 1

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"Empresas: {company_total}")
        self.stdout.write(f"Perfiles de negocio / empleados: {profile_total}")
        self.stdout.write(f"Tarjetas de presentacion: {business_card_total}")
        self.stdout.write(f"Websites: {website_total}")
        self.stdout.write(f"White Card Job: {job_total}")

    def get_user(self, User, username, full_name, email):
        first_name, *rest = full_name.split(" ")
        last_name = " ".join(rest)
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.set_password("CardbookDemo123!")
        user.save()
        return user
