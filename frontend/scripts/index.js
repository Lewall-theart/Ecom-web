$(document).ready(function() {
    // register form toggle
    $("#show-register").click(function() {
        $("#login-form").hide();
        $("#register-form").show();
    });


    // login form toggle
    $("#show-login").click(function() {
        $("#register-form").hide();
        $("#login-form").show();
    });


    // login button handling
    $("#login-btn").click(function() {
        let email = $("#login-email").val();

        if (!is_email(email)) {
            alert("Not a valid email!");
        }
        else {
            let password = $("#login-password").val();

            if (email && password) {
                $.ajax({
                    url: "http://127.0.0.1:5000/login",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({ email: email, password: password }),
                    success: function(response) {
                        if (response.session_string) {
                            sessionStorage.setItem("session_string", response.session_string);
                            
                            if (response.role == "admin") {
                                window.open("./admin.html", "_self");
                            } else if (response.role == "user") {
                                window.open("./home.html", "_self");
                            } else {
                                alert("Invalid role.");
                            }
                        } else {
                            alert(response.message);
                        }
                    },
                    error: function() {
                        alert("Error during login request.");
                    }
                });
            } else {
                alert("Missing data. Please fill in all fields.");
            }
        }
    });


    // register button handling
    $("#register-btn").click(function() {
        let email = $("#register-email").val();

        if (!is_email(email)) {
            alert("Not a valid email!");
        }
        else {
            let name = $("#register-name").val();
            let password = $("#register-password").val();

            if (name && email && password) {
                $.ajax({
                    url: "http://127.0.0.1:5000/register",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({ name: name, email: email, password: password }),
                    success: function(response) {
                        alert(response.message);

                        if (response.status == "success") {
                            alert("Please login to your new account.");
                            $("#register-form").hide();
                            $("#login-form").show();
                        }
                    },
                    error: function() {
                        alert("Error during registration request.");
                    }
                });
            } else {
                alert("Missing data. Please fill in all fields.");
            }
        }
    });
});
