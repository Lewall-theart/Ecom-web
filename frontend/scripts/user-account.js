$(document).ready(function() {
    // logout handling
    $("#logout-button").click(function() {
        if (confirm("Are you sure you want to logout?")) {
            sessionStorage.setItem("session_string", "");
            window.open("./index.html", "_self");
        }
    });


    // session string validation request
    let session_string = sessionStorage.getItem("session_string");
    if (session_string != null && session_string != "") {
        $.ajax({
            url: "http://127.0.0.1:5000/validate_session",
            headers: {
                "Auth-Token": session_string
            },
            type: "POST",
            contentType: "application/json",
            success: function(response) {
                // alert(response.message);
                if (response.status == "fail") {
                    alert("Session string validation failed");
                    sessionStorage.setItem("session_string", "");
                    window.open("./index.html", "_self");
                }

                display_user_info();
            },
            error: function() {
                alert("Error during session string validation.");
                sessionStorage.setItem("session_string", "");
                window.open("./index.html", "_self");
            }
        });
    } else {
        alert("Must be logged in to access page.");
        window.open("./index.html", "_self");
    }


    // get and display user information
    function display_user_info() {
        let sess_str = sessionStorage.getItem("session_string");
        $.ajax({
            url: "http://127.0.0.1:5000/get_info_from_session",
            headers: {
                "Auth-Token": sess_str
            },
            type: "GET",
            success: function(response) {
                if (response.status == "success") {
                    let account = response.account;
                    $("#account-id-field").val(account.id);
                    $("#name-input").val(account.name);
                    $("#email-input").val(account.email);
                }
            },
            error: function() {
                alert("Error during get info from session string request.")
            }
        });
    }

    $("#user-account-form").submit(function(event) {
        event.preventDefault(); // prevent send request and reload page

        const account_id = $("#account-id-field").val();
        const name = $("#name-input").val();
        const email = $("#email-input").val();
        const old_password = $("#old-password-input").val();
        const new_password = $("#new-password-input").val();

        $.ajax({
            url: "http://127.0.0.1:5000/user_edit_info",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ id: account_id, name: name, email: email, old_password: old_password, new_password: new_password }),
            success: function(response) {
                if (response.status === "success") {
                    alert("Account info update success: " + response.message);
                    sessionStorage.setItem("session_string", response.session_string);
                    display_user_info();
                } else {
                    alert("Failed to update account: " + response.message);
                }
            },
            error: function() {
                alert("Error updating account.");
            }
        });
    });
});
