### Codebeschrijving

**Advanced Software Quality Management System**

Dit systeem is ontworpen voor "Unique Meal," een dieet- en fitnesscentrum dat gepersonaliseerde maaltijdplannen, trainingsschema's en gezondheidsadvies biedt. De software richt zich op het veilig en betrouwbaar beheren van ledeninformatie en het bieden van een beveiligde ervaring aan gebruikers.

**Belangrijkste functies:**

1. **Ledenbeheer en Authentificatie**:
   - Het systeem beheert klantgegevens en biedt beveiligde authenticatieprocessen, inclusief wachtwoordhashing en versleuteling via RSA, om gevoelige informatie te beschermen.
   - De gebruikersinterface biedt verschillende toegangsniveaus en functies voor rollen zoals beheerder en consultant.

2. **Geavanceerde Inputvalidatie en Softwarekwaliteit**:
   - **SQL Injection Preventie**: Detecteert en blokkeert SQL-injectiepatronen in gebruikersinvoer door verdachte woorden en symbolen te controleren, zoals `SELECT`, `DROP`, `AND`, en SQL-commando's.
   - **Command Injection Bescherming**: Herkent en voorkomt uitvoeringscommando's (zoals `rm` en `shutdown`) om ongeautoriseerde systeemtoegang te voorkomen.
   - **XSS Bescherming**: Detecteert scriptinvoegingen (zoals `<script>` tags) en inline eventhandlers om Cross-Site Scripting (XSS) aanvallen te verhinderen.
   - **Buffer Overflow Preventie**: Limiteert de maximale invoerlengte voor alle velden om buffer overflow-aanvallen te voorkomen.
   - **Path Traversal Detectie**: Blokkeert padtraversale patronen zoals `../` om toegang tot gevoelige bestanden te beperken.
   - **Encoding- en Obfuscatiecontrole**: Controleert op URL-encoded en Base64-inhoud om te voorkomen dat gebruikers invoer verbergen die mogelijk gevaarlijk is.
   - **Null Byte Bescherming**: Detecteert null bytes en andere ongebruikelijke escape-sequenties in invoer die in bepaalde aanvallen worden gebruikt.

3. **Uitgebreide Validatieregels voor Gegevensintegriteit**:
   - Specifieke validatieregels voor verschillende gebruikersgegevens, waaronder:
     - **Naam**: Maximaal 15 karakters, alleen letters en spaties.
     - **E-mail**: Volgt een specifiek e-mailpatroon en heeft een maximumlengte.
     - **Adres**: Alleen letters, cijfers, komma's, en punten.
     - **Leeftijd**: Acceptabele waarden zijn tussen 18 en 125 jaar.
     - **Gewicht**: Beperkt tot waarden tussen 0 en 500 kg.
     - **Mobiel nummer**: Controleert op 8 cijfers.
     - **Geslacht**: Alleen vooraf bepaalde opties zoals "male", "female", "other".

4. **API Gateway en Toegangscontrole**:
   - Een beveiligde API Gateway regelt de toegang van verschillende gebruikers en biedt gedetailleerde autorisatie voor functies.

5. **Logging en Beveiligingsbewaking**:
   - Alle verdachte activiteiten, inclusief verdachte inputpatronen, worden gelogd voor controle en auditing. Gebruikers zonder beheerdersrechten worden automatisch uitgelogd bij detectie van beveiligingsrisico’s.

**Technische specificaties:**
- **Taal**: Python
- **Beveiligingsmodules**: Inputvalidatie, wachtwoordbeheer met bcrypt, RSA-versleuteling.
- **Doel van het systeem**: Gegevensintegriteit en bescherming tegen veelvoorkomende beveiligingsrisico's zoals SQL-injecties, XSS, en command-injecties.
- **Gebruikersrollen en toegang**: Gedefinieerde rollen zoals administrator, consultant, en gebruiker, elk met specifieke toegangsrechten en beperkingen.

