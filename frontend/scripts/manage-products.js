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
                                <td>${escape_html(product.name)}</td>
                                <td>${product.price}</td>
                                <td>${product.amount}</td>
                                <td>${product.description}</td>
                                <td>
                                    <button class="edit-button" data-id="${product.id}">Edit</button>
                                    <button class="delete-button" data-id="${product.id}">Delete</button>
                                </td>
                            </tr>
                        `;
                        product_body.append(row);
                    });

                    // delete button handling
                    $(".delete-button").click(function() {
                        const product_id = $(this).data("id");
                        delete_product(product_id);
                    });

                    // edit button handling
                    $(".edit-button").click(function() {
                        const product_id = $(this).data("id");
                        edit_product(product_id);
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


    // product deletion handling
    function delete_product(product_id) {
        if (confirm("Are you sure you want to delete this product?")) {
            $.ajax({
                url: `http://127.0.0.1:5000/delete_product?id=${product_id}`,
                headers: {
                    "Auth-Token": sessionStorage.getItem("session_string")
                },
                type: "DELETE",
                success: function(response) {
                    alert(response.message);
                    if (response.status === "success") {
                        load_products();
                    }
                },
                error: function() {
                    alert("Error during product deletion request.");
                }
            });
        }
    }


    // product editing handling
    function edit_product(product_id) {
        $.ajax({
            url: `http://127.0.0.1:5000/get_product?id=${product_id}`,
            type: "GET",
            success: function(response) {
                if (response.status == "success") {
                    const product = response.product;
                    const current_name = product.name;
                    const current_price = product.price;
                    const current_amount = product.amount;
                    const current_description = product.description;

                    // populate edit modal with product details
                    $("#edit-product-id").val(product_id);
                    $("#edit-product-name").val(current_name);
                    $("#edit-product-price").val(current_price);
                    $("#edit-product-amount").val(current_amount);
                    $("#edit-product-description").val(current_description);

                    // show edit product modal
                    $("#edit-product-modal").show();
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert("Failed to fetch product.");
            }
        });
    }

    // edit product form handling
    $("#edit-product-form").submit(function(event) {
        event.preventDefault(); // prevent reload page

        const product_id = $("#edit-product-id").val();
        const name = $("#edit-product-name").val();
        const price = $("#edit-product-price").val();
        const amount = $("#edit-product-amount").val();
        const description = $("#edit-product-description").val();

        $.ajax({
            url: "http://127.0.0.1:5000/edit_product",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ id: product_id, name: name, price: price, amount: amount, description: description }),
            success: function(response) {
                if (response.status === "success") {
                    alert(response.message);
                    load_products(); // reload product list
                    $("#edit-product-modal").hide();
                } else {
                    alert("Failed to update product: " + response.message);
                }
            },
            error: function() {
                alert("Error updating product.");
            }
        });
    });

    // cancel edit button handling
    $("#cancel-edit").click(function() {
        $("#edit-product-modal").hide();
    });


    // create product form handling
    $("#create-product-form").submit(function(event) {
        event.preventDefault(); // prevent reload page

        const name = $("#create-product-name").val();
        const price = $("#create-product-price").val();
        const amount = $("#create-product-amount").val();
        const description = $("#create-product-description").val();

        $.ajax({
            url: "http://127.0.0.1:5000/create_product",
            headers: {
                "Auth-Token": sessionStorage.getItem("session_string")
            },
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ name: name, price: price, amount: amount, description: description }),
            success: function(response) {
                if (response.status === "success") {
                    alert(response.message);
                    load_products(); // reload the product list
                    $("#create-product-modal").hide();
                } else {
                    alert("Failed to create product.");
                }
            },
            error: function() {
                alert("Error creating product: " + response.message);
            }
        });
    });

    // create product button handling
    $("#create-product-button").click(function() {
        $("#create-product-modal").show();
    });

    // cancel create product button handling
    $("#cancel-create").click(function() {
        $("#create-product-modal").hide();
    });
});
