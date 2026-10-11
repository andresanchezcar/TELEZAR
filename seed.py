"""
Crea la base de datos y llena el contenido inicial del sitio.

Uso:
    python seed.py          # crea tablas y siembra contenido de ejemplo
"""

import os
from datetime import date

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import (
    Brand,
    Category,
    Certificate,
    GalleryImage,
    Page,
    Product,
    Service,
    Setting,
    User,
    unique_slug,
)

app = create_app()

SETTINGS = [
    # (key, label, section, field_type, value)
    ("site_name", "Nombre del sitio", "Identidad", "text", "TELEZAR COMUNICACIONES"),
    ("site_tagline", "Eslogan", "Identidad", "text",
     "Soluciones integrales en redes, fibra optica y telecomunicaciones"),
    ("site_logo", "Logo", "Identidad", "image", ""),
    ("favicon", "Favicon", "Identidad", "image", ""),

    ("hero_badge", "Insignia del hero", "Hero (Inicio)", "text",
     "Especialistas en fibra optica"),
    ("hero_title", "Titulo principal", "Hero (Inicio)", "text",
     "Reparacion, Mantenimiento y Certificacion de Equipos de Fibra Optica"),
    ("hero_subtitle", "Subtitulo", "Hero (Inicio)", "textarea",
     "Fusionadoras, OTDR, cortadoras, identificadores de trafico, OPM y mas equipos de cualquier tipo y marca. Contamos con el equipo humano y tecnico que su compania necesita."),
    ("hero_image", "Imagen/ilustracion", "Hero (Inicio)", "image", ""),

    ("about_title", "Titulo seccion Nosotros", "Sobre nosotros", "text",
     "TELEZAR COMUNICACIONES"),
    ("about_text", "Texto", "Sobre nosotros", "textarea-big",
     "Contamos con el equipo humano y tecnico que necesita su compania para acceder a lo ultimo de la tecnologia en instalacion, mantenimiento, soporte tecnico, certificacion, calibracion y reparacion de maquinas de empalme y demas equipos de fibra optica."),
    ("about_image", "Imagen", "Sobre nosotros", "image", ""),
    ("about_badge_number", "Numero del distintivo", "Sobre nosotros", "text", "+10"),
    ("about_badge_text", "Texto del distintivo", "Sobre nosotros", "text",
     "anos de experiencia"),

    ("mission", "Mision", "Mision / Vision / Garantia", "textarea-big",
     "La mision de TELEZAR COMUNICACIONES es generar y fomentar soluciones que satisfagan las necesidades de nuestros clientes en el area de redes y telecomunicaciones, comprometiendonos con puntualidad, compromiso, eficiencia, eficacia y actitud positiva de parte de nuestros empleados, para asi lograr la permanencia en el mercado y obtener beneficios para nuestra sociedad."),
    ("vision", "Vision", "Mision / Vision / Garantia", "textarea-big",
     "La vision de TELEZAR COMUNICACIONES es ser una empresa lider en la prestacion de servicios de instalacion, mantenimiento, soporte tecnico, certificacion, calibracion y reparacion de maquinas de empalme, cortadoras, pinzas de trafico, OPM, VFL, OTDR y todo lo referente al servicio de laboratorio en equipos de telecomunicaciones."),
    ("guarantee", "Garantia", "Mision / Vision / Garantia", "textarea-big",
     "En concordancia con su mision, TELEZAR COMUNICACIONES se compromete a prestar un servicio en las areas de redes, camaras de vigilancia y telecomunicaciones de optima calidad, soportado en la implementacion, mantenimiento y mejoramiento continuo, con la participacion activa de personal calificado y comprometido con los principios y valores de la empresa."),

    ("phone", "Telefono principal", "Contacto", "text", "310 302 4059"),
    ("phone2", "Telefono secundario", "Contacto", "text", "314 324 9399"),
    ("whatsapp", "WhatsApp (solo numeros, ej. 573103024059)", "Contacto", "text",
     "573103024059"),
    ("address", "Direccion", "Contacto", "text", "Bogota, Colombia"),
    ("schedule", "Horario de atencion", "Contacto", "text",
     "Lunes a sabado, 24 horas de disponibilidad"),
    ("email_general", "Correo general", "Contacto", "text",
     "gerencia@telezarcomunicaciones.com"),
    ("email_ventas", "Correo de ventas", "Contacto", "text",
     "ventas@telezarcomunicaciones.com"),
    ("email_soporte", "Correo de soporte tecnico", "Contacto", "text",
     "soportetecnico@telezarcomunicaciones.com"),
    ("email_infosoporte", "Correo de informacion/soporte", "Contacto", "text",
     "infosoporte@telezarcomunicaciones.com"),

    ("facebook", "Facebook (URL)", "Redes sociales", "text",
     "https://www.facebook.com/profile.php?id=100008873479315"),
    ("twitter", "Twitter (URL)", "Redes sociales", "text", "https://twitter.com/TELEZAR4"),
    ("linkedin", "LinkedIn (URL)", "Redes sociales", "text", ""),
    ("instagram", "Instagram (URL)", "Redes sociales", "text", ""),

    ("catalog_text_venta", "Texto de la pagina de Ventas", "Catalogo", "textarea",
     "Ademas de capacitaciones y entrenamiento, en TELEZAR le podemos vender los articulos que necesita para que su proyecto sea un exito. Consulte precios y disponibilidad por WhatsApp."),
    ("catalog_text_alquiler", "Texto de la pagina de Alquiler", "Catalogo", "textarea",
     "Contamos con equipos con los cuales puede realizar sus trabajos, y nosotros se los alquilamos. Disponibilidad sujeta a revision."),

    ("cert_title", "Titulo seccion certificados", "Certificados", "text",
     "Genera tu certificado"),
    ("cert_text", "Texto seccion certificados", "Certificados", "textarea",
     "Digite el numero de serie del equipo para consultar y descargar su certificado."),

    ("footer_text", "Texto del pie de pagina", "Pie de pagina", "textarea",
     "Empresa especializada en instalacion, mantenimiento, soporte tecnico, certificacion, calibracion y reparacion de equipos de fibra optica."),
    ("copyright", "Linea de copyright", "Pie de pagina", "text",
     "TELEZAR COMUNICACIONES"),
]

PAGES = [
    {
        "slug": "nosotros",
        "title": "Nosotros",
        "subtitle": "Deseamos que sepas quienes somos, porque lo hacemos y para quien lo hacemos",
        "show_in_nav": True,
        "order": 1,
        "body": """
<h2>Objetivos</h2>
<p><strong>Generales:</strong> Ser lideres en la prestacion de servicios de mantenimiento preventivo, correctivo, reparacion, calibracion y ajuste mecanico de los diferentes equipos de fibra optica.</p>
<h3>Especificos</h3>
<ul>
<li>Alcanzar un crecimiento empresarial en la prestacion del servicio para posicionarnos en el area de redes, camaras de vigilancia, seguridad y telecomunicaciones, innovando con la tecnologia actual.</li>
<li>Contar con los mejores equipos, instrumentos de medicion y maquinaria de fibra optica.</li>
<li>Disponer del mejor portafolio de servicios de telecomunicaciones para garantizar a nuestros clientes seguridad y tranquilidad al escogernos.</li>
<li>Lograr un posicionamiento de marca empresarial para ser reconocidos esencialmente por nuestros clientes.</li>
</ul>
<h2>Mision</h2>
<p>Generar y fomentar soluciones que satisfagan las necesidades de nuestros clientes en el area de redes y telecomunicaciones, comprometiendonos con puntualidad, compromiso, eficiencia, eficacia y actitud positiva de parte de nuestros empleados.</p>
<h2>Vision</h2>
<p>Ser una empresa lider en la prestacion de instalacion, mantenimiento, soporte tecnico, certificacion, calibracion y reparacion de maquinas de empalme, cortadoras, pinzas de trafico, OPM, VFL, OTDR y todo en cuanto al servicio de laboratorio en equipos de telecomunicaciones.</p>
<h2>Compromiso empresarial</h2>
<p>En concordancia con su mision, TELEZAR COMUNICACIONES se compromete a prestar un servicio en las areas de redes y telecomunicaciones de optima calidad, soportado en la implementacion, mantenimiento y mejoramiento continuo y con la participacion activa de personal calificado.</p>
<h2>Lineamientos generales</h2>
<ul>
<li>Aumentar la satisfaccion de nuestros clientes.</li>
<li>Mantener un excelente ambiente laboral y operativo.</li>
<li>Mejorar constantemente el ambito financiero para garantizar la sostenibilidad y el crecimiento de nuestra empresa.</li>
</ul>
""",
    },
    {
        "slug": "capacitaciones",
        "title": "Capacitaciones y entrenamiento",
        "subtitle": "Formacion practica para el trabajo con fibra optica",
        "show_in_nav": True,
        "order": 3,
        "body": """
<p>En TELEZAR COMUNICACIONES contamos con el equipo humano que le ensena, capacita y guia en el arduo pero hermoso trabajo de redes y fibra optica.</p>
<h3>Entrenamiento practico</h3>
<p>Capacitaciones basadas en un 90% de practica, dirigidas a estudiantes, docentes, tecnicos y operarios de equipos de fibra optica, con el proposito de que desarrollen destrezas en el manejo de instrumentos y la elaboracion de proyectos para la instalacion e implementacion de fibra optica.</p>
<h3>Que aprenderas</h3>
<ul>
<li>Empalmaria por fusion y conectorizacion.</li>
<li>Preparacion de cajas de empalme, ODF, bandejas de terminacion y sangrias.</li>
<li>Enrutamiento y aprovisionamiento de redes de fibra optica.</li>
<li>Uso de unidades opticas, cortadoras de precision, OTDR y medidores de potencia.</li>
<li>Tendido de fibra optica subterranea, aerea autosoportada (ADSS), interior y exterior.</li>
</ul>
<p>Tenemos el equipo tecnico y humano que cuenta con la experiencia y experticia para que aprendas a usar unidades opticas, cortadoras de precision y muchos mas.</p>
""",
    },
    {
        "slug": "soporte",
        "title": "Centro de Soporte Tecnico (CST)",
        "subtitle": "Reparacion y mantenimiento de sus equipos de fibra optica",
        "show_in_nav": True,
        "order": 4,
        "body": """
<p>En nuestro Centro de Soporte Tecnico reparamos y mantenemos fusionadoras, OTDR, cortadoras, identificadores de trafico, OPM y otros equipos de fibra optica de cualquier tipo y marca.</p>
<h3>Nuestros servicios del CST</h3>
<ul>
<li>Cambio de electrodos.</li>
<li>Ajuste de unidad optica.</li>
<li>Ajuste de motores.</li>
<li>Ajuste de unidad de alineacion.</li>
<li>Ajuste de unidad de horno.</li>
<li>Ajuste de cortadora de precision.</li>
<li>Reemplazo de piezas desgastadas o rotas.</li>
<li>Verificacion de funcionamiento de baterias y cargadores.</li>
<li>Actualizacion de firmware.</li>
<li>Limpieza general de empalmadoras y de precision.</li>
<li>Limpieza de maletin de transporte.</li>
</ul>
<blockquote>Los instrumentos comprobados y calibrados periodicamente son esenciales para garantizar el correcto funcionamiento de su equipo.</blockquote>
""",
    },
]

SERVICES = [
    {
        "title": "Instalacion y empalmaria de fibra optica",
        "icon": "fiber",
        "featured": True,
        "order": 1,
        "excerpt": "Empalmaria por fusion, conectorizacion, preparacion de cajas de empalme, ODF, bandejas de terminacion, sangrias y enrutamientos.",
        "body": "Servicio tecnico en aprovisionamiento, alistamiento y mantenimiento de redes de fibra optica, incluye empalmaria por fusion, conectorizacion, preparacion de cajas de empalme, ODF, bandejas de terminacion, sangrias y enrutamientos.",
    },
    {
        "title": "Tendido de fibra optica",
        "icon": "network",
        "featured": False,
        "order": 2,
        "excerpt": "Tendido de fibra optica en areas subterraneas canalizadas, aereas autosoportadas (ADSS), interior y exterior.",
        "body": "Tendido de fibra optica en areas subterraneas a traves de canalizaciones, areas aereas autosoportadas (ADSS) e instalaciones interior/exterior, cumpliendo las normas del sector.",
    },
    {
        "title": "Certificacion y pruebas con OTDR",
        "icon": "cert",
        "featured": True,
        "order": 3,
        "excerpt": "Certificacion y pruebas de enlaces opticos con OTDR y medidores de potencia para la entrega a satisfaccion de los proyectos.",
        "body": "Certificacion y pruebas de enlaces opticos con instrumentos como OTDR (Optical Time Domain Reflectometer), revision de enlaces de fibra optica y entrega de resultados para la certificacion de los proyectos ejecutados.",
    },
    {
        "title": "Cuadrillas moviles 24/7",
        "icon": "support",
        "featured": False,
        "order": 4,
        "excerpt": "Suministro de cuadrillas moviles equipadas para empalmaria, tendido y obras civiles, por proyectos, horas, dias o meses.",
        "body": "Suministro de cuadrillas moviles equipadas y acondicionadas para trabajos de empalmaria, tendido y obras civiles, por proyectos, horas, dias o meses, segun la necesidad del cliente, con disponibilidad las 24 horas y los fines de semana.",
    },
    {
        "title": "Reparacion y mantenimiento de equipos",
        "icon": "tools",
        "featured": True,
        "order": 5,
        "excerpt": "Reparacion y mantenimiento de fusionadoras, OTDR, cortadoras, identificadores de trafico, OPM y otros equipos de fibra optica.",
        "body": "Reparacion y mantenimiento de fusionadoras, OTDR, cortadoras, identificadores de trafico, OPM y otros equipos de fibra optica de cualquier tipo y marca, en nuestro Centro de Soporte Tecnico.",
    },
    {
        "title": "Capacitacion y entrenamiento",
        "icon": "train",
        "featured": False,
        "order": 6,
        "excerpt": "Capacitaciones 90% practicas para estudiantes, docentes, tecnicos y operarios de equipos de fibra optica.",
        "body": "Capacitacion basada en un 90% de practica dirigida a estudiantes, docentes, tecnicos y operarios de equipos de fibra optica, con el proposito de que desarrollen destrezas en el manejo de instrumentos y la elaboracion de proyectos de instalacion e implementacion de fibra optica.",
    },
]

CATEGORIES = [
    ("Equipos de medicion y empalme", 1),
    ("Herramientas", 2),
    ("Insumos y repuestos", 3),
]

PRODUCTS = [
    {
        "name": "OTDR: reflectometro de dominio de tiempo optico",
        "category": "Equipos de medicion y empalme",
        "availability": "ambos",
        "price": None,
        "featured": True,
        "summary": "Reflectometro optico para certificacion y revision de enlaces de fibra optica.",
        "description": "Equipo profesional para medicion y certificacion de enlaces de fibra optica. Ideal para contratistas, instaladores y empresas de telecomunicaciones. Incluye cargador, maletin de transporte y accesorios.",
    },
    {
        "name": "Fusionadora de fibra optica",
        "category": "Equipos de medicion y empalme",
        "availability": "ambos",
        "price": None,
        "featured": True,
        "summary": "Fusionadora para empalme de fibra optica de todas las marcas.",
        "description": "Maquina de empalme por fusion para redes de fibra optica. Antes de la entrega se verifica su alineacion, unidad optica, horno y firmaware.",
    },
    {
        "name": "Electrodos para fusionadora (todas las marcas)",
        "category": "Insumos y repuestos",
        "availability": "venta",
        "price": 180000,
        "featured": False,
        "summary": "Electrodos de alta calidad compatibles con las principales marcas de fusionadoras.",
        "description": "Paquete de electrodos para fusionadoras de fibra optica. Compatibles con Fujikura, Fitel, Sumitomo, Innova, Signal y mas. Garantia de calidad y duracion.",
    },
    {
        "name": "Alicates pelacables de fibra optica / Stripper",
        "category": "Herramientas",
        "availability": "venta",
        "price": 85000,
        "featured": False,
        "summary": "Pinza pelacables de precision para recubrimientos de fibra optica.",
        "description": "Alicate stripper de precision para retirar el recubrimiento primario de la fibra optica sin danar el nucleo. Imprescindible para empalmaria y conectorizacion.",
    },
    {
        "name": "Medidor de potencia optica (OPM)",
        "category": "Equipos de medicion y empalme",
        "availability": "ambos",
        "price": None,
        "featured": False,
        "summary": "Medidor de potencia optica para verificacion de niveles de senal.",
        "description": "Medidor OPM para verificar la potencia de los enlaces de fibra optica. Calibrado y verificado en nuestro laboratorio.",
    },
    {
        "name": "Cortadora de precision (cleaver)",
        "category": "Herramientas",
        "availability": "ambos",
        "price": None,
        "featured": False,
        "summary": "Cortadora de precision para corte limpio de fibra optica.",
        "description": "Cortadora cleaver de precision que garantiza angulos de corte optimos para empalmes de baja perdida.",
    },
    {
        "name": "Cajas de empalme, ODF y bandejas",
        "category": "Insumos y repuestos",
        "availability": "venta",
        "price": None,
        "featured": False,
        "summary": "Bandejas de terminacion y organizacion para redes de fibra optica.",
        "description": "Cajas de empalme, ODF y bandejas de terminacion para la organizacion y proteccion de empalmes en redes de fibra optica.",
    },
    {
        "name": "Pinza identificadora de trafico (VFL)",
        "category": "Equipos de medicion y empalme",
        "availability": "ambos",
        "price": None,
        "featured": False,
        "summary": "Identificador de trafico y localizador visual de fallas.",
        "description": "Pinza identificadora de trafico y localizador visual de fallas (VFL) para verificar continuidad e identificar hilos en redes de fibra optica.",
    },
]

BRANDS = [
    "DVP", "Fitel", "Fujikura", "Iino", "KOM", "Multicom",
    "Promax", "Signal", "Sky", "Sumitomo", "Telecom",
]

CERTIFICATES = [
    {
        "serial": "27AM1701",
        "client": "Empresa de telecomunicaciones",
        "equipment": "Fusionadora de fibra optica",
        "issued_date": date(2024, 11, 20),
        "notes": "Certificacion de calibracion y ajuste de unidad optica.",
    },
    {
        "serial": "TZC0738",
        "client": "Contratista de redes",
        "equipment": "OTDR",
        "issued_date": date(2024, 10, 2),
        "notes": "Verificacion de calibracion de reflectometro OTDR.",
    },
]


def seed():
    with app.app_context():
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

        # --- Tablas -----------------------------------------------------
        if not tables:
            db.create_all()
            print("* Tablas creadas en la base de datos.")
        else:
            db.create_all()
            print("* Tablas verificadas.")

        # --- Administrador ---------------------------------------------
        if User.query.count() == 0:
            username = os.environ.get("ADMIN_USERNAME", "admin")
            password = os.environ.get("ADMIN_PASSWORD", "admin123")
            email = os.environ.get("ADMIN_EMAIL", "admin@telezarcomunicaciones.com")
            admin = User(username=username, email=email)
            admin.set_password(password)
            admin.full_name = "Administrador Telezar"
            db.session.add(admin)
            print(f"* Usuario administrador creado: {username} / {password}")
        else:
            print("* Usuarios ya existentes.")

        # --- Ajustes ----------------------------------------------------
        if Setting.query.count() == 0:
            for key, label, section, ftype, value in SETTINGS:
                db.session.add(Setting(
                    key=key, label=label, section=section, field_type=ftype, value=value,
                ))
            print(f"* {len(SETTINGS)} ajustes creados.")
        else:
            print("* Ajustes ya existentes.")

        # --- Paginas ----------------------------------------------------
        if Page.query.count() == 0:
            for p in PAGES:
                db.session.add(Page(
                    slug=p["slug"],
                    title=p["title"],
                    subtitle=p["subtitle"],
                    body=p["body"],
                    show_in_nav=p["show_in_nav"],
                    order=p["order"],
                ))
            print(f"* {len(PAGES)} paginas creadas.")
        else:
            print("* Paginas ya existentes.")

        # --- Servicios --------------------------------------------------
        if Service.query.count() == 0:
            for s in SERVICES:
                db.session.add(Service(
                    title=s["title"],
                    slug=unique_slug(Service, s["title"]),
                    icon=s["icon"],
                    excerpt=s["excerpt"],
                    body=s["body"],
                    featured=s["featured"],
                    order=s["order"],
                ))
            print(f"* {len(SERVICES)} servicios creados.")
        else:
            print("* Servicios ya existentes.")

        # --- Categorias y productos -------------------------------------
        if Category.query.count() == 0:
            cats = {}
            for name, order in CATEGORIES:
                cat = Category(name=name, slug=unique_slug(Category, name), order=order)
                cats[name] = cat
                db.session.add(cat)
            print(f"* {len(CATEGORIES)} categorias creadas.")

            if Product.query.count() == 0:
                for p in PRODUCTS:
                    db.session.add(Product(
                        name=p["name"],
                        slug=unique_slug(Product, p["name"]),
                        summary=p["summary"],
                        description=p["description"],
                        price=p["price"],
                        category=cats[p["category"]],
                        availability=p["availability"],
                        featured=p["featured"],
                    ))
                print(f"* {len(PRODUCTS)} productos creados.")
        else:
            print("* Categorias/proyectos ya existentes.")

        # --- Marcas -------------------------------------------------------
        if Brand.query.count() == 0:
            for i, name in enumerate(BRANDS):
                db.session.add(Brand(name=name, order=i))
            print(f"* {len(BRANDS)} marcas creadas.")
        else:
            print("* Marcas ya existentes.")

        # --- Certificados -------------------------------------------------
        if Certificate.query.count() == 0:
            for c in CERTIFICATES:
                db.session.add(Certificate(**c))
            print(f"* {len(CERTIFICATES)} certificados de ejemplo creados.")
        else:
            print("* Certificados ya existentes.")

        # --- Galeria ------------------------------------------------------
        if GalleryImage.query.count() == 0:
            for i in range(1, 7):
                db.session.add(GalleryImage(
                    title=f"Trabajo de empalmaria {i}",
                    image="/static/img/placeholder.svg",
                    album="Proyectos",
                    order=i,
                ))
            print("* 6 imagenes de galeria de ejemplo creadas.")
        else:
            print("* Galeria ya existente.")

        db.session.commit()
        print("\nListo. Ejecute 'python run.py' y abra http://127.0.0.1:5000")
        print("Panel de administracion: http://127.0.0.1:5000/admin")


if __name__ == "__main__":
    seed()