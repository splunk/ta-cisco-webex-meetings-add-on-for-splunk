document.addEventListener("DOMNodeInserted", function (event) {

    if (event.target.innerHTML && event.target.innerHTML.startsWith("<form")) {
        const redirect_uri = event.target.querySelector("[data-name='redirect_uri']");
        const client_secret = event.target.querySelector("[data-name='client_secret']");

        // Enter the default redirect_url
        if(redirect_uri) {
            const full_url_arr = window.location.href.split("/");
            const default_redirect_url = `${full_url_arr[0]}/${full_url_arr[1]}/${full_url_arr[2]}/${full_url_arr[3]}/splunkd/__raw/services/cisco-webex-meetings-oauth`;

            const replace_text = 'placeholder="https://{{hostname}}/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth"';
            const new_input_val = `placeholder="${default_redirect_url}" value="${default_redirect_url}"`;
            redirect_uri.innerHTML = redirect_uri.innerHTML.replace(replace_text, new_input_val);
        }

        // Add the Generate Tokens Button
        if (client_secret) {
            const replace_text = "Generate tokens by clicking the below button";
            const generate_token_button="<div><button type='button' style='background: rgb(26, 137, 41);color: rgb(255, 255, 255);font-size: 14px;border-color: transparent;' onclick=clickEvent()>Generate Tokens</button></div>";
            client_secret.innerHTML = client_secret.innerHTML.replace(replace_text, generate_token_button);
        }
    }
}, false);


function clickEvent() {
    const client_id = $("[data-name='client_id'] > div > div > div input").val();
    const client_secret = $("[data-name='client_secret'] > div > div > div input").val();
    const redirect_uri =$("[data-name='redirect_uri'] > div > div > div input").val();

    // POST creds to Splunk backend for further use
    var settings = {
        "url": "/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth",
        "method": "POST",
        "timeout": 0,
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"

        },
        "data": $.param({ "redirect_uri": redirect_uri, "client_id": client_id, "client_secret": client_secret }),
    };
    $.ajax(settings).done(function (response) {
        console.log("response", response["method"]);
    });

    // Send User to Webex side to get grant
    url = `https://api.webex.com/v1/oauth2/authorize?client_id=${client_id}&response_type=code&redirect_uri=${redirect_uri}&scope=all_read&state=set_state_here&code_challenge=abc&code_challenge_method=plain`
    console.log("[-] Clicked URL : " + url);
    window.open(url, 'popup', 'width=700,height=700');
    return false;
}