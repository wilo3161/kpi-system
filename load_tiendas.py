import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.manager import local_db

tiendas_data = [
  {
    "Nombre de Tienda": "Aeropostale - Milagro",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "MILAGRO",
    "Contacto": "Lady Silva",
    "Dirección": "Av. 12 de Octubre, entre presidente Jerónimo Carrión y presidente Javier Espi",
    "Teléfono": "0985415948"
  },
  {
    "Nombre de Tienda": "Aeropostale - Peso Shopping Riobamba",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "RIOBAMBA",
    "Contacto": "María Fernanda Ibarra",
    "Dirección": "Av. Antonio José de Sucre frente a la Universidad UNACH CC Paseo Shopping",
    "Teléfono": "0993438844"
  },
  {
    "Nombre de Tienda": "Aeropostale - Multiplaza Riobamba",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "RIOBAMBA",
    "Contacto": "Jennifer Jimenez",
    "Dirección": "Avenida Lizarzaburu y Agustin Torres - CC Multiplaza Riobamba",
    "Teléfono": "0962636619"
  },
  {
    "Nombre de Tienda": "Aeropostale - Pasaje",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "PASAJE",
    "Contacto": "Jhonny Cun",
    "Dirección": "Av. Quito entrada a Pasaje y Redondel del León - Junto a Super Aki Pasaje",
    "Teléfono": "0969586186"
  },
  {
    "Nombre de Tienda": "Aeropostale - Paseo Ambato",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "AMBATO",
    "Contacto": "Franco Torres",
    "Dirección": "Av.Pio Baroja Nesi y Av. Manuelita Saéns Paseo Shoping Ambato",
    "Teléfono": "0984951515"
  },
  {
    "Nombre de Tienda": "Aeropostale - Pedernales",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "PEDERNALES",
    "Contacto": "Mónica Muñoz",
    "Dirección": "Av. García Moreno y Calle Pedernales - Junto a Aki Pedernales",
    "Teléfono": "0989113061"
  },
  {
    "Nombre de Tienda": "Aeropostale - Península",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "PENINSULA",
    "Contacto": "Kenny Bohorquez",
    "Dirección": "Av. Carlos Espinosa y Av. Central CC Paseo Shopping La Peninsula",
    "Teléfono": "0997432684"
  },
  {
    "Nombre de Tienda": "Aeropostale - Playas",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "PLAYAS",
    "Contacto": "Steven Ortiz",
    "Dirección": "Av. General Villamil - Paseo Shoping Playas",
    "Teléfono": "0991871477"
  },
  {
    "Nombre de Tienda": "Aeropostale - (Cuenca) Mall del Rio",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "CUENCA",
    "Contacto": "Adrian",
    "Dirección": "Av. Felipe II y Autopista Sur - CC Mall del Rio",
    "Teléfono": "0984752711"
  },
  {
    "Nombre de Tienda": "Aeropostale - 6 de Diciembre",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUITO",
    "Contacto": "Micaela Yépez",
    "Dirección": "Av. 6 de Diciembre y Thomas de Berlanga CC Riocentro UIO",
    "Teléfono": "0987883889"
  },
  {
    "Nombre de Tienda": "Aeropostale - Ambato",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "AMBATO",
    "Contacto": "Gabriela Urrutia",
    "Dirección": "Av. Atahualpa y Victor Hugo CC Mall de los Andes",
    "Teléfono": "0967239488"
  },
  {
    "Nombre de Tienda": "Aeropostale - Babahoyo",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "BABAHOYO",
    "Contacto": "Yomaira Sellan",
    "Dirección": "Av.Enrique Ponce Luque CC Paseo Shopping Babahoyo",
    "Teléfono": "0981841355"
  },
  {
    "Nombre de Tienda": "Aeropostale - bombolí",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "SANTO DOMINGO",
    "Contacto": "Josselyn Navarrete",
    "Dirección": "Via Chone Diagonal a la Universidad Catolica CC Bombolí Shopping",
    "Teléfono": "0939906346"
  },
  {
    "Nombre de Tienda": "Aeropostale - Bahía de Caráquez",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "BAHIA DE CARAQUE",
    "Contacto": "Nayely Orejuela",
    "Dirección": "Av. 3 de Noviembre - CC Paseo Shoping Bahía de caraquez",
    "Teléfono": "0981131760"
  },
  {
    "Nombre de Tienda": "Aeropostale - Carapungo",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUITO",
    "Contacto": "María José Benalcazar",
    "Dirección": "Av. Simón Bolívar, Panamericana Norte y calle, Capitán Giovanni Calles - CC",
    "Teléfono": "0997242323"
  },
  {
    "Nombre de Tienda": "Aeropostale - CCI",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUITO",
    "Contacto": "Carolina Procel",
    "Dirección": "Av. Amazonas y Naciones Unidas - CC Iñaquito",
    "Teléfono": "0984048928"
  },
  {
    "Nombre de Tienda": "Aeropostale - Ceibos",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Angie Delgado",
    "Dirección": "Av. Del Bombero y San Eduardo - Riocentro Ceibos",
    "Teléfono": "0999085369"
  },
  {
    "Nombre de Tienda": "Aeropostale - Centro Histórico",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "CUENCA",
    "Contacto": "Renata Sacari",
    "Dirección": "Av. Simón Bolívar y PadreA guirre Centro Histórico diagonal a a la chocolateria",
    "Teléfono": "0980874018"
  },
  {
    "Nombre de Tienda": "Price Club - City Mall",
    "Empresa": "Price Club",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Jordan Guale",
    "Dirección": "Av. felipe Pezo y Av. Benjamín Carrión CC City Mall",
    "Teléfono": "0962880194"
  },
  {
    "Nombre de Tienda": "Aeropostale - Condado Shopping",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUITO",
    "Contacto": "Mateo Recalde",
    "Dirección": "Av. Mariscal Sucre entre Av. La Prensa Y Jhon F. Kennedy - CC Condado Sh",
    "Teléfono": "0993736447"
  },
  {
    "Nombre de Tienda": "Aeropostale - Daule",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "DAULE",
    "Contacto": "Alisson Ramirez",
    "Dirección": "Av. Vicente Piedrahita y Coronel Calletano Cestaris- Paseo Shoping Daule",
    "Teléfono": "0978881886"
  },
  {
    "Nombre de Tienda": "Aeropostale - Dorado",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Oscar Alvarado",
    "Dirección": "Av. León Febres Cordero Ribadeneyra - Rio Centro Dorado",
    "Teléfono": "0959098012"
  },
  {
    "Nombre de Tienda": "Aeropostale - Durán",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "DURAN",
    "Contacto": "Yaritza Córdova",
    "Dirección": "Av. Boliche Panamericana - Paseo Shoping Durán Junto al Terminal",
    "Teléfono": "0996359344"
  },
  {
    "Nombre de Tienda": "Aeropostale - el Coca",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "EL COCA",
    "Contacto": "Adriana Zurita",
    "Dirección": "Av. 9 de Octubre y Río Curaray - Junto a Super Akí el Coca",
    "Teléfono": "0989137928"
  },
  {
    "Nombre de Tienda": "Aeropostale - La Plaza",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "IBARRA",
    "Contacto": "Andrea Andrango",
    "Dirección": "Av. Mariano Acosta entre Inacio Canelos y Víctor Gómez Jurado - CC La Plaza",
    "Teléfono": "0978765143"
  },
  {
    "Nombre de Tienda": "Aeropostale - Lago Agrio",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "LAGO AGRIO",
    "Contacto": "Angie Maldonado",
    "Dirección": "Av. Quito y Pasaje Brazil - Junto a Super Aki Lago Agrio",
    "Teléfono": "0989893309"
  },
  {
    "Nombre de Tienda": "Aeropostale - Machala",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "MACHALA",
    "Contacto": "Iris carpio",
    "Dirección": "Av. Paquisha y Vía Machala km  2 1/2 - CC Paseo Shoping Machala",
    "Teléfono": "0997260162"
  },
  {
    "Nombre de Tienda": "Aeropostale - Mall del Pacífico",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "MANTA",
    "Contacto": "Karina Figueroa",
    "Dirección": "Av. Malecón y Calle 23 - CC Mall del Pacífico",
    "Teléfono": "0990614279"
  },
  {
    "Nombre de Tienda": "Aeropostale - Mall del Río (Gye)",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Danna Peralta",
    "Dirección": "Av. Francisco de Orellana y Av. Guillermo Pareja - CC Mall del Río",
    "Teléfono": "0995609664"
  },
  {
    "Nombre de Tienda": "Aeropostale - Mall del Sol",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Kiara Dávalos",
    "Dirección": "Av. Juan tanca marengo, Carlos Aurelio Rubira Infante 14 NE y Pasaje 1A - C",
    "Teléfono": "0992753549"
  },
  {
    "Nombre de Tienda": "Aeropostale - Mall del Sur",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Judith Asunción",
    "Dirección": "AV 25 de Julio junto al Hospital de IESS -  CC Mall del Sur",
    "Teléfono": "0996869429"
  },
  {
    "Nombre de Tienda": "Aeropostale - Manta",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "MANTA",
    "Contacto": "Yenny Alvia",
    "Dirección": "Av. 4 de noviembre Paseo Shoping Manta",
    "Teléfono": "0995168732"
  },
  {
    "Nombre de Tienda": "Aeropostale - Portoviejo",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "PORTOVIEJO",
    "Contacto": "Gissel Loor",
    "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo",
    "Teléfono": "0963683962"
  },
  {
    "Nombre de Tienda": "Aeropostale - Rio Centro Norte",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Doris Zambrano",
    "Dirección": "Av. Francisco de Orellana y Urb. Alcance CC Riocentro Norte",
    "Teléfono": "0969705137"
  },
  {
    "Nombre de Tienda": "Aeropostale - San Luis",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUITO",
    "Contacto": "Karina Proaño",
    "Dirección": "Av. General Rumiñahui y Av. San Luis - CC San Luis Shoping",
    "Teléfono": "0991879974"
  },
  {
    "Nombre de Tienda": "Aeropostale - Santo Domingo",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "SANTO DOMINGO",
    "Contacto": "Mateo Fruto",
    "Dirección": "Av. Abraham Calazacón y Av. Quito - Paseo Shoping Santo Domingo",
    "Teléfono": "0967593039"
  },
  {
    "Nombre de Tienda": "Aeropostale - Cayambe",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "CAYAMBE",
    "Contacto": "Celeste Contreras",
    "Dirección": "Panamericana norte y camino del sol CC Altos de Cayambe",
    "Teléfono": "0995414136"
  },
  {
    "Nombre de Tienda": "Aeropostale - Quevedo",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "QUEVEDO",
    "Contacto": "Dayana León",
    "Dirección": "Av. Quito, frente a la policia Nacional CC Paseo Shopping Quevedo",
    "Teléfono": "0981398074"
  },
  {
    "Nombre de Tienda": "Price Club - Portoviejo",
    "Empresa": "Price Club",
    "Origen": "MATRIZ",
    "Destino": "PORTOVIEJO",
    "Contacto": "Dayana Merchan",
    "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo",
    "Teléfono": "0959877997"
  },
  {
    "Nombre de Tienda": "Price Club - Machala",
    "Empresa": "Price Club",
    "Origen": "MATRIZ",
    "Destino": "MACHALA",
    "Contacto": "Yuleysi Delgado",
    "Dirección": "AV. 25 de Junio CC Oro Plaza",
    "Teléfono": "0998087085"
  },
  {
    "Nombre de Tienda": "Price Club - Guayaquil",
    "Empresa": "Price Club",
    "Origen": "MATRIZ",
    "Destino": "GUAYAQUIL",
    "Contacto": "Angie Delgado",
    "Dirección": "Pedro Carbo S/N y Luque junto a almacenes Estuardo Sánchez",
    "Teléfono": "0999085369"
  },
  {
    "Nombre de Tienda": "Price Club - Ibarra",
    "Empresa": "Price Club",
    "Origen": "MATRIZ",
    "Destino": "IBARRA",
    "Contacto": "Silvia Urcuango",
    "Dirección": "Av. Victor Gómez Jurado y Rodrigo Miño junto a la cancha La Bombonera",
    "Teléfono": "0982649058"
  },
  {
    "Nombre de Tienda": "Aeropostale - Altos del Rio",
    "Empresa": "Aeropostale",
    "Origen": "MATRIZ",
    "Destino": "CUENCA",
    "Contacto": "Marco Eras",
    "Dirección": "Av. Felipe II y Autopista Sur - CC Mall Altos del Rio",
    "Teléfono": "0994570933"
  }
]

if __name__ == "__main__":
    # Cargar a DB
    existentes = local_db.find("tiendas", {})
    if not existentes:
        print("Cargando tiendas a la base de datos...")
        for t in tiendas_data:
            local_db.insert("tiendas", t)
        print(f"Se cargaron {len(tiendas_data)} tiendas.")
    else:
        print("Las tiendas ya existen en la BD.")

    # Generar usuarios base para el administrador (para que no pierda acceso si se resetea DB)
    admins = local_db.find("users", {"role": "Administrador"})
    if not admins:
        import hashlib
        pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
        local_db.insert("users", {"username": "admin", "password": pw_hash, "role": "Administrador", "full_name": "Administrador General", "active": True})
        print("Usuario admin creado.")
