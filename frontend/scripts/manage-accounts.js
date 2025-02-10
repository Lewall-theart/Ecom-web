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
                if (response.status == "fail") {
                    alert("Session string validation failed");
                    sessionStorage.setItem("session_string", "");
                    window.open("./index.html", "_self");
                }

                if (response.role != "admin") {
                    alert("Invalid role. Please log into an admin account to access the admin page.");
                    window.open("./index.html", "_self");
                }

                load_accounts();
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


    // account loading handling
    function load_accounts() {
        $.ajax({
            url: "http://127.0.0.1:5000/get_accounts",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "GET",
            success: function(response) {
                if (response.status === "success") {
                    const accounts = response.accounts;
                    const account_body = $("#account-body");
                    account_body.empty(); // clear existing rows

                    // loop through accounts and create table rows
                    accounts.forEach(function(account) {
                        buttons = "";

                        if (account.role !== "admin") {
                            buttons = `
                                <button class="edit-button" data-id="${account.id}">Edit</button>
                                <button class="delete-button" data-id="${account.id}">Delete</button>
                            `;
                        } else {
                            buttons = `
                                <button class="edit-button" data-id="${account.id}">Edit Password</button>
                            `;
                        }

                        const row = `
                            <tr id="account-${account.id}">
                                <td>${account.id}</td>
                                <td>${escape_html(account.name)}</td>
                                <td>${escape_html(account.email)}</td>
                                <td>${account.password}</td>
                                <td>${account.role}</td>
                                <td>${buttons}</td>
                            </tr>
                        `;
                        account_body.append(row);
                    });

                    // delete button handling
                    $(".delete-button").click(function() {
                        const account_id = $(this).data("id");
                        delete_account(account_id);
                    });

                    // edit button handling
                    $(".edit-button").click(function() {
                        const account_id = $(this).data("id");
                        edit_account(account_id);
                    });
                } else {
                    alert("Failed to fetch accounts.");
                }
            },
            error: function() {
                alert("Error fetching accounts.");
            }
        });
    }


    // account deletion handling
    function delete_account(account_id) {
        if (confirm("Are you sure you want to delete this account?")) {
            $.ajax({
                url: `http://127.0.0.1:5000/delete_account?id=${account_id}`,
                headers: {
                    "Auth-Token": sessionStorage.getItem("session_string")
                },
                type: "DELETE",
                success: function(response) {
                    alert(response.message);
                    if (response.status == "success") {
                        load_accounts();
                    }
                },
                error: function() {
                    alert("Error during account deletion request.");
                }
            });
        }
    }


    // edit account handling
    function edit_account(account_id) {
        $.ajax({
            url: `http://127.0.0.1:5000/get_account?id=${account_id}`,
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "GET",
            success: function(response) {
                if (response.status == "success") {
                    const account = response.account;
                    const current_name = account.name;
                    const current_email = account.email;

                    // populate edit modal with account details
                    $("#edit-account-id").val(account_id);
                    $("#edit-account-name").val(current_name);
                    $("#edit-account-email").val(current_email);
                    $("#edit-account-password").val("");

                    if (account.role == "admin") {
                        $("#edit-account-name").hide();
                        $("#edit-account-email").hide();
                        $("label[for='edit-account-name']").hide();
                        $("label[for='edit-account-email']").hide();
                        $("#edit-account-old-password").show();
                        $("label[for='edit-account-old-password']").show();
                        $("#edit-account-header").html("Edit Password");
                    } else {
                        $("#edit-account-name").show();
                        $("#edit-account-email").show();
                        $("label[for='edit-account-name']").show();
                        $("label[for='edit-account-email']").show();
                        $("#edit-account-old-password").hide();
                        $("label[for='edit-account-old-password']").hide();
                    }

                    // show edit account modal
                    $("#edit-account-modal").show();
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert("Failed to fetch account.");
            }
        });
    }

    // edit account form handling
    $("#edit-account-form").submit(function(event) {
        event.preventDefault(); // prevent reload page

        const account_id = $("#edit-account-id").val();
        const name = $("#edit-account-name").val();
        const email = $("#edit-account-email").val();
        const password = $("#edit-account-password").val();
        const old_password = $("#edit-account-old-password").val();

        $.ajax({
            url: "http://127.0.0.1:5000/edit_account",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ id: account_id, name: name, email: email, password: password, old_password: old_password }),
            success: function(response) {
                if (response.status === "success") {
                    alert(response.message);
                    
                    if (response.session_string) {
                        sessionStorage.setItem("session_string", response.session_string);
                    }

                    load_accounts(); // reload account list
                    $("#edit-account-modal").hide();
                } else {
                    alert("Failed to update account: " + response.message);
                }
            },
            error: function() {
                alert("Error updating account.");
            }
        });
    });

    // cancel edit button handling
    $("#cancel-edit").click(function() {
        $("#edit-account-modal").hide();
    });


    // create account form handling
    $("#create-account-form").submit(function(event) {
        event.preventDefault(); // prevent reload page

        const name = $("#create-account-name").val();
        const email = $("#create-account-email").val();
        const password = $("#create-account-password").val();

        $.ajax({
            url: "http://127.0.0.1:5000/create_account",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ name: name, email: email, password: password }),
            success: function(response) {
                if (response.status === "success") {
                    alert(response.message);
                    load_accounts(); // reload the account list
                    $("#create-account-modal").hide();
                } else {
                    alert("Failed to create account.");
                }
            },
            error: function() {
                alert("Error creating account: " + response.message);
            }
        });
    });

    // create account button handling
    $("#create-account-button").click(function() {
        $("#create-account-modal").show();
    });

    // cancel create account button handling
    $("#cancel-create").click(function() {
        $("#create-account-modal").hide();
    });
});
