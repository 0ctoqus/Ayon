function clean_string(text){
  if (text.length == 0) {
    return "";
  }

  var diactricMap = {
   "ö": "o", "ü": "u", "ó": "o", "ő": "o", "ú": "u", "é": "e", "á": "a", "à": "a", "ű": "u", 
   "í": "i", "Ö": "O", "Ü": "U", "Ó": "O", "Ő": "O", "Ú": "U", "É": "E", "Á": "A", "À": "A", 
   "Ű": "U", "Í": "I", "ç": "c", "Ç": "C"
   };
  var diactrics = Object.keys(diactricMap);
  
  for (var diactricIndex = 0; diactricIndex < diactrics.length; diactricIndex++) {
    var from = diactrics[diactricIndex];
    var to = diactricMap[from];
    text = text.replace(from, to);
  }
  
  text = text.replace(/(\n|\r|<[^>]+>)/g,"")
  text = text.replace(/\s+/g," ")
  return text;
}

function get_messages(){
  var threads = GmailApp.search('label:unread label:inbox');
  var data = [];

  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();

    for (var j = 0; j < messages.length; j++) {
      var message = messages[j]
      var date = message.getDate();
      var subject = message.getSubject();
      var body = message.getPlainBody();
      data.push([Utilities.formatDate(date, 'Europe/Paris', 'MM-dd-yy'),
                 Utilities.formatDate(date, 'Europe/Paris', 'HH:mm:ss'),
                 clean_string(subject), 
                 clean_string(body).substring(0, 80)])
    }
  }
  return data;
}

function save_to_drive(jsonFile){  
  Logger.log("Looking for file to override")
  //var files = DriveApp.searchFiles("trashed=true and title='automated_unread_mail.csv'");
  var files = DriveApp.getTrashedFiles();
  while (files.hasNext()){
    var file = files.next();
    var name = file.getName();
    Logger.log(name);
    if (name == "automated_unread_mail.json"){
      Logger.log(jsonFile)
      file.setContent(jsonFile);
      Logger.log("Overwrited file content");
      break;
    }
  }
}

function MoveUnreadToDrive(){
  Logger.log("Fetching messages");
  var data = get_messages();
  Logger.log("Got " + data.length + " messages");
  
  Logger.log("Generating json");
  var jsonFile = JSON.stringify(data);
  Logger.log("Got json");
  
  Logger.log("Saving to drive");
  save_to_drive(jsonFile);
  Logger.log("Done");
}
