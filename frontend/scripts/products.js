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

                load_products();
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


    // product loading handling
    function load_products() {
        $.ajax({
            url: "http://127.0.0.1:5000/get_products",
            type: "GET",
            success: function(response) {
                if (response.status === "success") {
                    const products = response.products;
                    const product_body = $("#product-body");
                    product_body.empty(); // clear existing rows

                    // loop through products and create table rows
                    products.forEach(function(product) {
                        const row = `
                            <tr id="product-${product.id}">
                                <td>${product.id}</td>
                                <td>${product.name}</td>
                                <td>${product.price}</td>
                                <td>${product.amount}</td>
                                <td>${product.description}</td>
                                <td>
                                    <input type="number" class="product-amount" id="amount-${product.id}" min="1" value="1">
                                </td>
                                <td>
                                    <button class="add-to-cart-button" data-id="${product.id}">Add to cart</button>
                                </td>
                            </tr>
                        `;
                        product_body.append(row);
                    });

                    // add to cart button handling
                    $(".add-to-cart-button").click(function() {
                        const product_id = $(this).data("id");
                        const amount = parseInt($(`#amount-${product_id}`).val());
                        add_product_to_cart(product_id, amount);
                    });
                } else {
                    alert("Failed to fetch products.");
                }
            },
            error: function() {
                alert("Error fetching products.");
            }
        });
    }


    function get_id_from_session_str(session_string) {
        let user_id;
        
        $.ajax({
            url: "http://127.0.0.1:5000/get_info_from_session",
            headers: {
                "Auth-Token": session_string
            },
            type: "GET",
            contentType: "application/json",
            async: false,
            success: function(response) {
                if (response.status == "success") {
                    const account = response.account;
                    user_id = account.id;
                }
            },
            error: function() {
                alert("Error during get info from session request.");
            }
        });

        return user_id;
    }

    function add_product_to_cart(product_id, amount) {
        const user_id = get_id_from_session_str(sessionStorage.getItem("session_string"));

        $.ajax({
            url: "http://127.0.0.1:5000/add_to_cart",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ product_id: product_id, user_id: user_id, amount: amount }),
            success: function(response) {
                if (response.status == "success") {
                    alert("Added product to cart.");
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert("Error during add to cart.")
            }
        });
    }
});
