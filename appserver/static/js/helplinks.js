document.addEventListener("DOMNodeInserted", function (event) {

    if (event.target.className && event.target.className.startsWith("form-")) {
        h = event.target.querySelector('.help-block')
        if (h) {
            replace_text = "by clicking the below button";
            h.innerHTML = h.innerHTML.replace(replace_text, "<div><a href='#' class='btn btn-primary' onclick=clickEvent()>Generate Tokens</a>");
        }
    }
}, false);

function clickEvent() {
    let client_id = getInputValue('additional_parameters-client_id')
    let client_secret = getInputValue('additional_parameters-client_secret')
    let redirect_uri = getInputValue('additional_parameters-redirect_uri')

    var settings = {
        "url": "/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth",
        "method": "POST",
        "timeout": 0,
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"

        },
        "data": $.param({ "redirect_uri": redirect_uri, "client_id": client_id, "client_secret": client_secret}),
        // JSON.stringify() -> applicaiton/json
    };
    $.ajax(settings).done(function (response) {
        console.log("response", response["method"]);
    });
    // fetch / ajax / xhr
    // let redirect_uri = `http://${hostname}:${splunk_web_port}/${splunk_site}/splunkd/__raw/services/cisco-webex-meetings-oauth`
    console.log("redirect_uri", redirect_uri)
    url = `https://api.webex.com/v1/oauth2/authorize?client_id=${client_id}&response_type=code&redirect_uri=${redirect_uri}&scope=all_read&state=set_state_here&code_challenge=abc&code_challenge_method=plain`
    console.log("Clicked URL : " + url);
    window.open(url, 'popup', 'width=700,height=700');
    // window.open(url);
    return false;
}

function getInputValue(inputId) {
    let inputBox = document.getElementById(inputId);
    inputBox.onkeyup = function () {
        let inputValue = this.value;
        return inputValue
    }
    let inputValue = inputBox.onkeyup()
    return inputValue
}



