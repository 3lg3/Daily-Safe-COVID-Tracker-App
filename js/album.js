'use strict'

var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition
var recognition = new SpeechRecognition();
var recognizing = false
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-US';

var vocieSearching = ""

// AWS API
var sdk = apigClientFactory.newClient({});

// initial picture
getAllPictures()


document.querySelector('#search').addEventListener('click', (e) => {
    var searchinput = ""
    if(recognizing) {
        recognition.stop();
        searchinput = vocieSearching
        recognizing = false
    }else{
        searchinput = document.getElementById("search-content").value
    }
    if(searchinput == ""){
        getAllPictures()
    }
    else{
        getSearchPictures(searchinput)
    }
    document.getElementById("search-content").value = ""
})

document.querySelector('#upload').addEventListener('click', (e)=>{
    let tages = document.getElementById("tages").value.replace(/ /g, '').split(",");
    let file = document.getElementById("files").files;
    
    if((file.length)==0){
      alert("add an image");
      return;
    }
    const reader = new FileReader();
    reader.readAsDataURL(file[0]);
    reader.onload = function () {
        var result = reader.result;
        var content= result.substr(result.indexOf(',')+1); 
      
        var formData = {
        "content":content,
        "filename":file[0].name,
        "tags": tages
        }
        sendPictures(formData)
    };

    document.getElementById("tages").value = ""
    reader.onerror = function (error) {
      alert("add an image");
    };
})

document.querySelector('#voice').addEventListener('click', (e)=>{
    vocieSearching = ""
    recognizing = true
    recognition.start()
    console.log('Ready to listen');
})

recognition.onresult = function(event){
    for (var i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
            vocieSearching = vocieSearching.concat(event.results[i][0].transcript)
        }
      }
}

recognition.onerror = function(event) {
    console.log('onerror', event);
}

recognition.onspeechend = function() {
    recognizing = false
    recognition.stop
}
