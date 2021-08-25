'use strict'
const getAllPictures = () => {
    console.log("Sending search: all ")
    getPicturesFetch("allPictures","allPictures").then((response) => {
        if(response.status == 200){
            console.log(response)
            var data = response.data
            renderPictures(data)
        }else{
            throw new Error("Unable to fetch")
        }
    })
}

const getSearchPictures = (searchContain) => {
    console.log("Sending search: ", searchContain)
    getPicturesFetch("searchPictures", searchContain).then((response) => {
        if(response.status == 200){
            console.log("search: ",response)
            var data = response.data
            renderPictures(data)
        }else{
            throw new Error("Unable to fetch")
        } 
    })
}

const getPicturesFetch = (type, searchinput) => {
    var params = {}
    var body = {}
    var additionalParams = {
        headers:{
            'Content-Type': "application/json"
        },
        queryParams: {
            'q': searchinput,
        }
    }


    return sdk.pictureGet(params, body, additionalParams);
}

const sendPictures = (formdata) => {
    sendPicturesFetch(formdata).then((response) => {
        if(response.status == 200){
            console.log(response)
        }else{
            throw new Error("Unable to upload")
        }
    })
}

const sendPicturesFetch = (formdata) => {
    return sdk.picturePost({},formdata,{})
}

const generatePictureDOM = (pictureURL) => {
    const pictureEl = document.createElement('a')
    const imageEl = document.createElement('img')
    imageEl.src = pictureURL
    imageEl.classList.add("image")
    pictureEl.appendChild(imageEl)
    return pictureEl
}

const renderPictures = (pictures) => {
    const picturelistEL = document.querySelector("#pictures")
    picturelistEL.innerHTML = ''
    if(pictures){
        pictures.forEach((picURL) => {
            const picEl = generatePictureDOM(picURL)
            picturelistEL.appendChild(picEl)
        })
    }else{
        return
    }
}