function doGet(e) {
    // Require secret token
    if (e.parameter['token'] != 'your secret') {
      return ContentService.createTextOutput(e.parameter['token']);
      return;
    }
  
    const calendarId = 'primary';
    const now = new Date();
    const events = Calendar.Events.list(calendarId, {
      timeMin: now.toISOString(),
      singleEvents: true,
      orderBy: 'startTime',
      maxResults: 3
    });
    if (!events.items || events.items.length === 0) {
      Logger.log('No events found.');
      return ContentService.createTextOutput('No events');
    }
  
    var res = ''
    for (const event of events.items) {
      if (event.start.date) {
        // All-day event - show date
        const start = new Date(event.start.date);
        var day = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', day: '2-digit' });
        var month = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', month: '2-digit' });
        res += `${day}${month}. ${event.summary.substring(0,13)}\n`;
        continue;
      }
      // Event with time
      const start = new Date(event.start.dateTime);
      if (start.toDateString() == now.toDateString()) {
        // Todays event - show time
        var min = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', minute: '2-digit' });
        // Workaround for broken 2-digit minute formating
        if (min.length == 1) {
          min = '0' + min;
        }
        var hour = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', hour: '2-digit' })
        res += ` ${hour}:${min} ${event.summary.substring(0,13)}\n`;
      }
      else {
        // Future events - show date
        var day = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', day: '2-digit' });
        var month = start.toLocaleString('cs-CZ', { timeZone: 'Europe/Prague', month: '2-digit' });
        res += `${day}${month}. ${event.summary.substring(0,13)}\n`;
      }
    }
    Logger.log(res)
    return ContentService.createTextOutput(res);
  }