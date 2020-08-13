document.addEventListener("DOMNodeInserted", function (event) {

    if (event.target.className && event.target.className.startsWith("form-")) {
        // console.log("event.target", event.target)
        h = event.target.querySelector('.help-block')
        // console.log("h", h)
        if (h) {
            urlpat = "by clicking the below button";
            console.log("urlpat", urlpat)
            h.innerHTML = h.innerHTML.replace(urlpat, "<div><a href='#' class='btn btn-primary' onclick=clickEvent()>Generate Tokens</a>");
            // h.innerHTML = h.innerHTML.replace(urlpat, "<div><a href='#' onclick=clickEvent(https://api.webex.com/v1/oauth2/authorize?)><img alt=\"\"Add to Slack\"\" height='40' width='139' src='https://platform.slack-edge.com/img/add_to_slack.png' srcset='https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x' /></a></div>");
        }
    }
}, false);

function clickEvent() {
    var inputBox = document.getElementById('additional_parameters-client_id');
    // console.log("inputBox", inputBox)
    inputBox.onkeyup = function () {
        let client_id = this.value;
        console.log("client_id", client_id)
        return client_id
    }
    client_id = inputBox.onkeyup()
    let redirect_uri = "http://localhost:10060/oauth"
    url = `https://api.webex.com/v1/oauth2/authorize?client_id=${client_id}&response_type=code&redirect_uri=${redirect_uri}&scope=all_read+meeting_modify+recording_modify+user_modify+setting_modify&state=abc&code_challenge=abc&code_challenge_method=plain`
    console.log("Clicked URL : " + url);
    window.open(url, 'popup', 'width=700,height=700');
    return false;
}

