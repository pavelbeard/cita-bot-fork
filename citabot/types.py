import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from undetected_chromedriver import Chrome


__all__ = [
    "DocType",
    "OperationType",
    "Office",
    "Province",
    "Browsers",
    "CustomerProfile",
    "ConfirmedCita",
    "ICitaAction",
]


class DocType(str, Enum):
    DNI = "dni"
    NIE = "nie"
    PASSPORT = "passport"


class OperationType(str, Enum):
    AUTORIZACION_DE_REGRESO = "20"  # POLICIA-AUTORIZACIÓN DE REGRESO
    BREXIT = "4094"  # POLICÍA-EXP.TARJETA ASOCIADA AL ACUERDO DE RETIRADA CIUDADANOS BRITÁNICOS Y SUS FAMILIARES (BREXIT)
    CARTA_INVITACION = "4037"  # POLICIA-CARTA DE INVITACIÓN
    CERTIFICADOS_NIE = "4096"  # POLICIA-CERTIFICADOS Y ASIGNACION NIE
    CERTIFICADOS_NIE_NO_COMUN = (
        "4079"  # POLICIA-CERTIFICADOS Y ASIGNACION NIE (NO COMUNITARIOS)
    )
    CERTIFICADOS_RESIDENCIA = "4049"  # POLICIA-CERTIFICADOS (DE RESIDENCIA, DE NO RESIDENCIA Y DE CONCORDANCIA) #fmt: off
    CERTIFICADOS_UE = "4038"  # POLICIA-CERTIFICADO DE REGISTRO DE CIUDADANO DE LA U.E.
    RECOGIDA_DE_TARJETA = (
        "4036"  # POLICIA - RECOGIDA DE TARJETA DE IDENTIDAD DE EXTRANJERO (TIE)
    )
    SOLICITUD_ASILO = "4078"  # POLICIA - SOLICITUD ASILO
    TOMA_HUELLAS = "4010"  # POLICIA-TOMA DE HUELLAS (EXPEDICIÓN DE TARJETA) Y RENOVACIÓN DE TARJETA DE LARGA DURACIÓN
    ASIGNACION_NIE = "4031"  # Asignación de N.I.E.
    FINGERP_RINT = "4047"  # POLICÍA-EXPEDICIÓN DE TARJETAS CUYA AUTORIZACIÓN RESUELVE LA DIRECCIÓN GENERAL DE MIGRACIONES
    RENOVACION_ASILO = (
        "4067"  # POLICIA- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE SOLICITANTES DE ASILO
    )


class Office(str, Enum):
    # Barcelona
    BADALONA = "18"  # CNP-COMISARIA BADALONA, AVDA. DELS VENTS (9)
    BARCELONA = "16"  # CNP - RAMBLA GUIPUSCOA 74, RAMBLA GUIPUSCOA (74)
    BARCELONA_MALLORCA = "14"  # CNP MALLORCA-GRANADOS, MALLORCA (213)
    CASTELLDEFELS = "19"  # CNP-COMISARIA CASTELLDEFELS, PLAÇA DE L`ESPERANTO (4)
    CERDANYOLA = "20"  # CNP-COMISARIA CERDANYOLA DEL VALLES, VERGE DE LES FEIXES (4)
    CORNELLA = "21"  # CNP-COMISARIA CORNELLA DE LLOBREGAT, AV. SANT ILDEFONS, S/N
    ELPRAT = "23"  # CNP-COMISARIA EL PRAT DE LLOBREGAT, CENTRE (4)
    GRANOLLERS = "28"  # CNP-COMISARIA GRANOLLERS, RICOMA (65)
    HOSPITALET = (
        "17"  # CNP-COMISARIA L`HOSPITALET DE LLOBREGAT, Rbla. Just Oliveres (43)
    )
    IGUALADA = "26"  # CNP-COMISARIA IGUALADA, PRAT DE LA RIBA (13)
    MANRESA = "38"  # CNP-COMISARIA MANRESA, SOLER I MARCH (5)
    MATARO = "27"  # CNP-COMISARIA MATARO, AV. GATASSA (15)
    MONTCADA = "31"  # CNP-COMISARIA MONTCADA I REIXAC, MAJOR (38)
    RIPOLLET = "32"  # CNP-COMISARIA RIPOLLET, TAMARIT (78)
    RUBI = "29"  # CNP-COMISARIA RUBI, TERRASSA (16)
    SABADELL = "30"  # CNP-COMISARIA SABADELL, BATLLEVELL (115)
    SANTACOLOMA = "35"  # CNP-COMISARIA SANTA COLOMA DE GRAMENET, IRLANDA (67)
    SANTADRIA = "33"  # CNP-COMISARIA SANT ADRIA DEL BESOS, AV. JOAN XXIII (2)
    SANTBOI = "24"  # CNP-COMISARIA SANT BOI DE LLOBREGAT, RIERA BASTÉ (43)
    SANTCUGAT = "34"  # CNP-COMISARIA SANT CUGAT DEL VALLES, VALLES (1)
    SANTFELIU = "22"  # CNP-COMISARIA SANT FELIU DE LLOBREGAT, CARRERETES (9)
    TERRASSA = "36"  # CNP-COMISARIA TERRASSA, BALDRICH (13)
    VIC = "37"  # CNP-COMISARIA VIC, BISBE MORGADES (4)
    VILADECANS = "25"  # CNP-COMISARIA VILADECANS, AVDA. BALLESTER (2)
    VILAFRANCA = (
        "46"  # CNP COMISARIA VILAFRANCA DEL PENEDES, Avinguda Ronda del Mar, 109
    )
    VILANOVA = "39"  # CNP-COMISARIA VILANOVA I LA GELTRU, VAPOR (19)

    # Tenerife
    OUE_SANTA_CRUZ = "1"  # 1 OUE SANTA CRUZ DE TENERIFE,  C/LA MARINA, 20
    PLAYA_AMERICAS = "2"  # CNP-Playa de las Américas, Av. de los Pueblos, 2
    PUERTO_CRUZ = "3"  # CNP-Puerto de la Cruz/Los Realejos, Av. del Campo y Llarena, 3

    # Aicante
    ALCOY = "12"  # CNP Alcoy, Placeta Les Xiques, S/N, Alcoy
    ALICANTE_NIE = "15"  # CNP Alicante NIE, Ebanistería, 4-6, Alicante
    ALICNTE_TIE = "3"  # CNP Alicante TIE, Campo de Mirra, 6, Alicante
    ALICANTE_COMISARIA = (
        "13"  # CNP Comisaría Provincial, C/ Isabel la Católica, 25, Alicante
    )
    ALICANTE_EBANISTERIA = "1"  # CNP Ebanistería, Avda Marquesado, 53, Denia
    ALTEA = "2"  # OEX ALTEA, SAN ISIDRO LABRADOR, 1, ALTEA
    BENIDORM = "10"  # CNP Benidorm, Apolo XI, 36, Benidorm
    BENIDORM_TIE = "4"  # CNP Benidorm TIE, Callosa D`Ensarria, 2, Benidorm
    DENIA = "11"  # CNP Denia, Avda Marquesado, 53, Denia
    ELDA = "9"  # CNP Elda, Lamberto Amat, 26, Elda
    ORIHUELA = "7"  # CNP Orihuela, Sol, 34, Orihuela
    ORIHUELA_COSTA = (
        "14"  # CNP Orihuela Costa, C/ Flores (Centro de Emergencias), 5, Orihuela Costa
    )
    TORREVIEJA = "6"  # CNP Torrevieja, Arquitecto Larramendi, 3, Torrevieja


class Province(str, Enum):
    A_CORUÑA = "15"
    ALBACETE = "2"
    ALICANTE = "3"
    ALMERÍA = "4"
    ARABA = "1"
    ASTURIAS = "33"
    ÁVILA = "5"
    BADAJOZ = "6"
    BARCELONA = "8"
    BIZKAIA = "48"
    BURGOS = "9"
    CÁCERES = "10"
    CÁDIZ = "11"
    CANTABRIA = "39"
    CASTELLÓN = "12"
    CEUTA = "51"
    CIUDAD_REAL = "13"
    CÓRDOBA = "14"
    CUENCA = "16"
    GIPUZKOA = "20"
    GIRONA = "17"
    GRANADA = "18"
    GUADALAJARA = "19"
    HUELVA = "21"
    HUESCA = "22"
    ILLES_BALEARS = "7"
    JAÉN = "23"
    LA_RIOJA = "26"
    LAS_PALMAS = "35"
    LEÓN = "24"
    LLEIDA = "25"
    LUGO = "27"
    MADRID = "28"
    MÁLAGA = "29"
    MELILLA = "52"
    MURCIA = "30"
    NAVARRA = "31"
    ORENSE = "32"
    PALENCIA = "34"
    PONTEVEDRA = "36"
    SALAMANCA = "37"
    S_CRUZ_TENERIFE = "38"
    SEGOVIA = "40"
    SEVILLA = "41"
    SORIA = "42"
    TARRAGONA = "43"
    TERUEL = "44"
    TOLEDO = "45"
    VALENCIA = "46"
    VALLADOLID = "47"
    ZAMORA = "49"
    ZARAGOZA = "50"
    
class Browsers(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    OPERA = "opera"
    EDGE = "edge"


@dataclass
class CustomerProfile:
    name: str
    doc_type: DocType
    doc_value: str  # Passport? "123123123"; Nie? "Y1111111M"
    phone: str
    email: str
    province: Province = Province.BARCELONA
    operation_code: OperationType = OperationType.RENOVACION_ASILO
    country: str = "RUSIA"
    year_of_birth: Optional[str] = None
    offices: Optional[list] = field(default_factory=list)
    except_offices: Optional[list] = field(default_factory=list)

    anticaptcha_api_key: Optional[str] = None
    auto_captcha: bool = True
    auto_office: bool = True
    chrome_driver_path: str = "/usr/local/bin/chromedriver"
    chrome_profile_name: Optional[str] = None
    chrome_profile_path: Optional[str] = None
    min_date: Optional[str] = None  # "dd/mm/yyyy"
    max_date: Optional[str] = None  # "dd/mm/yyyy"
    min_time: Optional[str] = None  # "hh:mm"
    max_time: Optional[str] = None  # "hh:mm"
    save_artifacts: bool = False
    sms_webhook_token: Optional[str] = None
    wait_exact_time: Optional[list] = None  # [[minute, second]]
    reason_or_type: str = "solicitud de asilo"

    # Internals
    bot_result: bool = False
    first_load: Optional[bool] = True  # Wait more on the first load to cache stuff
    log_settings: Optional[dict] = field(default_factory=lambda: {"stream": sys.stdout})
    recaptcha_solver: Any = None
    image_captcha_solver: Any = None
    current_solver: Any = None
    
    # 
    proxy: Optional[bool] = False

    def __post_init__(self):
        if self.operation_code == OperationType.RECOGIDA_DE_TARJETA:
            assert (
                len(self.offices) == 1
            ), "Indicate the office where you need to pick up the card"


@dataclass
class ConfirmedCita:
    code: str  # justificante final
    screenshot: Optional[str] = None  # screenshot


class ICitaAction(ABC):
    @abstractmethod
    def do(self, driver: Chrome, context: CustomerProfile):
        pass
