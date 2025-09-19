function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    // Ota lukko (max 30 s)
    if (!lock.tryLock(30 * 1000)) {
      return jsonOut({ ok: false, error: "busy" });
    }

    // Perusvalidointi
    if (!e || !e.postData || !e.postData.contents) {
      return jsonOut({ ok: false, error: "no_postdata" });
    }

    console.log("[EventLogger] Payload: " + e.postData.contents);
    Logger.log("[EventLogger] Payload: %s", e.postData.contents);

    var parsed;
    try {
      parsed = JSON.parse(e.postData.contents);
    } catch (err) {
      return jsonOut({ ok: false, error: "invalid_json" });
    }

    var SS = SpreadsheetApp.openById('1-oITkBsKB6DJM5QJc7W_5y1tEFtfQ5ksVUbubjFnJ5Q');
    var sheet = SS.getSheetByName(parsed.sheet_name);
    if (!sheet) {
      sendEmail("tuomastutkija@gmail.com", "doPost virhe", "Taulukkoa ei löydy: " + parsed.sheet_name);
      return jsonOut({ ok: false, error: "sheet_not_found" });
    }

    // Odotetaan muotoa: "v0,v1,v2,v3,v4,v5,v6"
    var arr = String(parsed.values || "").split(",");
    if (arr.length < 7) {
      return jsonOut({ ok: false, error: "values_missing" });
    }

    // Parsitaan arvot
    var value0 = arr[0];                     // RSSI (teksti/numero)
    var value1 = toNum(arr[1]);              // Priority
    var value2 = toNum(arr[2]);              // IP (numero -> nimihaku)
    var value3 = toNum(arr[3]);              // EventCode
    var value4 = toNum(arr[4]);              // EventWord
    var value5 = toNum(arr[5]);              // Event Value
    var value6 = toNum(arr[6]);              // Lisäarvo (jaetaan sadalla)

    // Aika skriptin aikavyöhykkeellä
    var tz = Session.getScriptTimeZone();
    var date_now = Utilities.formatDate(new Date(), tz, "dd.MM.yyyy");
    var time_now = Utilities.formatDate(new Date(), tz, "HH:mm:ss");

    // Sarake C kuvaus prioriteetin mukaan (sama logiikka kuin alkuperäisessä)
    var statusC = "";
    switch (value1) {
      case 1:  statusC = "Hälytys tullut - Kriittinen"; break;
      case 2:  statusC = "Hälytys tullut"; break;
      case 3:  statusC = "Huomio!"; break;
      case 4:  statusC = "Huomio!"; break;
      case 99: statusC = "Hälytys poistunut - Kriittinen"; break;
      case 98: statusC = "Hälytys poistunut"; break;
      default: statusC = ""; break;
    }

    // Lisätään tyhjä rivi otsikon alle ja kirjoitetaan arvot kerralla
    sheet.insertRows(2, 1);
    var rowValues = [[
      date_now,                                // A
      time_now,                                // B
      statusC,                                 // C
      value0,                                  // D (RSSI)
      value1,                                  // E (Priority)
      GeneralLibrary.getDeviceName(value2),    // F (Laite / IP-nimi)
      GeneralLibrary.getEventName(value3),     // G (Tapahtuman nimi)
      value4,                                  // H (EventWord)
      value5,                                  // I (Event Value)
      value6 / 100.0                           // J
    ]];
    sheet.getRange(2, 1, 1, rowValues[0].length).setValues(rowValues);

    SpreadsheetApp.flush();
    return jsonOut({ ok: true });
  } catch (error) {
    sendEmail("tuomastutkija@gmail.com", "doPost virhe", error.toString());
    return jsonOut({ ok: false, error: "exception", message: String(error) });
  } finally {
    lock.releaseLock();
  }
}

/** Apuri: turvallinen numero-parsaus */
function toNum(x) {
  var n = Number(x);
  return isNaN(n) ? 0 : n;
}

/** Palauta JSON-teksti oikealla MIME-tyypillä */
function jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function sendEmail(recipient, subject, body) {
  MailApp.sendEmail(recipient, subject, body);
}
