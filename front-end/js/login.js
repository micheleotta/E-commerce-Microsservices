function login() {
    var email = document.getElementById("email-login").value;
    localStorage.setItem("email", email);

    document.getElementById("login-btn").style.display = "none";
    document.getElementById("logout-btn").style.display = "block";
}

function logout() {
    localStorage.removeItem("email");
    document.getElementById("login-btn").style.display = "block";
    document.getElementById("logout-btn").style.display = "none";
}

document.addEventListener('DOMContentLoaded', function() {
    var email = localStorage.getItem("email");
    
    if (email) {
        document.getElementById("login-btn").style.display = "none";
        document.getElementById("logout-btn").style.display = "block";
    }
});