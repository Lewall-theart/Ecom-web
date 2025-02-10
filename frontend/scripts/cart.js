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

                load_cart();
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


    // product loading handling
    function load_cart() {
        const user_id = get_id_from_session_str(sessionStorage.getItem("session_string"));

        $.ajax({
            url: `http://127.0.0.1:5000/get_cart?id=${user_id}`,
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "GET",
            success: function(response) {
                if (response.status === "success") {
                    const products = response.cart;
                    const cart_body = $("#cart-body");
                    cart_body.empty(); // clear existing rows

                    // loop through products and create table rows
                    products.forEach(function(product) {
                        const row = `
                            <tr id="product-${product.product_id}">
                                <td>${product.name}</td>
                                <td>${product.price}</td>
                                <td>
                                    <input type="number" class="product-amount" id="amount-${product.product_id}" min="1" value="${product.amount}">
                                </td>
                                <td>
                                    <button class="update-amount-button" data-id="${product.product_id}">Update amount</button>
                                    <button class="del-from-cart-button" data-id="${product.product_id}">Remove</button>
                                </td>
                            </tr>
                        `;
                        cart_body.append(row);
                    });

                    // update amount button handling
                    $(".update-amount-button").click(function() {
                        const product_id = $(this).data("id");
                        const amount = parseInt($(`#amount-${product_id}`).val());
                        update_amount(user_id, product_id, amount);
                    });

                    // delete from cart button handling
                    $(".del-from-cart-button").click(function() {
                        const product_id = $(this).data("id");
                        del_prod_from_cart(user_id, product_id);
                    });
                } else {
                    alert("Cart is empty. Add products to cart for purchasing.");
                    window.open("./products.html", "_self");
                }
            },
            error: function() {
                alert("Error fetching products.");
            }
        });
    }


    function update_amount(user_id, product_id, amount) {
        $.ajax({
            url: "http://127.0.0.1:5000/update_product_in_cart",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({user_id: user_id, product_id: product_id, amount: amount}),
            success: function(response) {
                if (response.stock_amount) {
                    alert(response.message + " Only " + response.stock_amount + " products available.");
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert("Error during update amount request.");
            }
        });
    }


    function del_prod_from_cart(user_id, product_id) {
        $.ajax({
            url: `http://127.0.0.1:5000/del_product_from_cart?user_id=${user_id}&product_id=${product_id}`,
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "DELETE",
            success: function(response) {
                if (response.status == "success") {
                    alert("Product was removed from cart.");
                    load_cart();
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert("Error during removal from cart request.");
            }
        });
    }


    $("#purchase-button").click(function() {
        const user_id = get_id_from_session_str(sessionStorage.getItem("session_string"));

        $.ajax({
            url: `http://127.0.0.1:5000/get_cart_total?user_id=${user_id}`,
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "GET",
            async: false,
            success: function(response) {
                if (response.status == "success") {
                    if (confirm("Total is " + response.total + ". Would to like to proceed with purchase?")) {
                        purchase_cart(user_id);
                    }
                }
            },
            error: function() {
                alert("Error during get cart total request.");
            }
        });
    });

    function purchase_cart(user_id) {
        $.ajax({
            url: "http://127.0.0.1:5000/purchase_product",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({user_id: user_id}),
            success: function(response) {
                alert(response.message);
                if (response.status == "success") {
                    alert("Removing purchased products from cart.");
                    load_cart();
                }
            },
            error: function() {
                alert("Error during purchase products request.");
            }
        });
    }
});
