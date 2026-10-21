# Instalación en la clínica (Windows)

Esta guía explica cómo instalar la app de citas en una computadora con Windows de la clínica
y cómo usarla desde las demás computadoras y celulares.

## Cómo funciona

- **Una PC hace de servidor.** Tiene el programa `ClinicaCitas.exe` y guarda todos los datos.
  Debe estar **encendida** para que los demás puedan usar la app.
- **Las demás PCs y celulares** no instalan nada: abren la app en el navegador (Chrome, Edge…),
  conectados al **mismo Wi-Fi o red** que el servidor. Todos ven la misma agenda.

## 1. Instalar en la PC servidor

1. Copia `ClinicaCitas-windows.zip` a la PC y descomprímelo en **`C:\ClinicaCitas`**.
   No lo pongas en "Archivos de programa": ahí Windows no deja guardar los datos.
2. Entra en `C:\ClinicaCitas\ClinicaCitas` y haz doble clic en **`ClinicaCitas.exe`**.
   - Se abre una ventana negra: **no la cierres**, es el servidor. Puedes minimizarla.
   - Si Windows SmartScreen muestra "Windows protegió su PC", pulsa **Más información → Ejecutar de todas formas**
     (pasa con programas que no están firmados digitalmente).
   - Si el Firewall de Windows pregunta, marca **Redes privadas** y pulsa **Permitir acceso**.
     Sin esto, las otras PCs no podrán entrar.
3. Se abre el navegador con la pantalla **Bienvenido**: el propietario crea su cuenta de administrador.
4. En la ventana negra aparece la dirección para las otras PCs, por ejemplo:
   `En las otras PCs y móviles: http://192.168.1.50:8501`. Anótala.

### Que se abra sola al encender la PC

1. Pulsa `Windows + R`, escribe `shell:startup` y pulsa Enter. Se abre la carpeta "Inicio".
2. Con el botón derecho sobre `ClinicaCitas.exe` → **Mostrar más opciones → Enviar a → Escritorio (crear acceso directo)**.
3. Mueve ese acceso directo del escritorio a la carpeta "Inicio".

### Que la dirección no cambie

El router puede darle otra IP a la PC servidor después de reiniciarla, y entonces las otras PCs
dejarían de encontrarla. Para evitarlo, en la configuración del router haz una **reserva DHCP**
(también llamada "IP fija" o "IP estática") para la PC servidor. Si no sabes hacerlo, pídelo a
quien instaló el internet de la clínica.

## 2. Usar la app desde otras PCs y celulares

- Conéctate al mismo Wi-Fi o red que el servidor y abre en el navegador la dirección anotada
  (por ejemplo `http://192.168.1.50:8501`).
- Para tenerla a mano en una PC: guárdala como **favorito**, o crea un acceso directo en el escritorio
  (botón derecho → Nuevo → Acceso directo → pega la dirección → nombre "Clínica - Citas").
- En el celular: ábrela en el navegador y elige **Agregar a pantalla de inicio**.
- Cada persona entra con su usuario. El administrador crea las cuentas del personal en **Usuarios**.

## 3. Copias de seguridad

- Todos los datos están en **`C:\ClinicaCitas\ClinicaCitas\datos\`** (`clinica.db`).
- Al usar **Reiniciar datos**, la app guarda antes una copia en `datos\respaldos\`.
- Copia la carpeta `datos\` completa a un USB o a la nube **cada semana** (o más seguido).
  Si la PC se daña, esa copia es lo único que permite recuperar los pacientes y las citas.
- Para restaurar una copia: cierra la ventana negra, reemplaza `datos\clinica.db` por la copia y vuelve a abrir el programa.

## 4. Instalar una versión nueva

1. Cierra la ventana negra del servidor.
2. Haz una copia de la carpeta `datos\` por seguridad.
3. Descomprime el ZIP nuevo encima, reemplazando los archivos, **pero sin borrar la carpeta `datos\`**.
4. Abre `ClinicaCitas.exe` otra vez.

## Seguridad

- La app guarda datos de salud de pacientes: usa contraseñas fuertes y una cuenta por persona.
- Dentro de la red, la conexión no va cifrada. Usa un **Wi-Fi con contraseña** y no el Wi-Fi de invitados.
- La app no se puede abrir desde fuera de la clínica: solo desde su red.

## Problemas frecuentes

| Problema | Solución |
|---|---|
| Las otras PCs no abren la dirección | Comprueba que el servidor esté encendido, la ventana negra abierta y que estén en la misma red. Revisa el Firewall de Windows: Panel de control → Firewall → "Permitir una aplicación" → `ClinicaCitas` con **Privada** marcada. |
| La dirección dejó de funcionar | La IP del servidor cambió: mira la nueva en la ventana negra y haz la reserva DHCP del paso 1. |
| Al abrir el programa solo se abre el navegador | Es normal: la app ya estaba abierta. |
| Olvidé la contraseña del personal | El administrador la restablece en **Usuarios**. |
