async function register() {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    console.log(document.getElementById("email"))
    console.log(document.getElementById("email").value)
    const password = document.getElementById("password").value;

    const res = await fetch("/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username,email, password })
    });

    const data = await res.json();
    alert(data.message);
}

async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const res = await fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (data.message === "Login success") {
        localStorage.setItem("user_id", data.user_id);
        document.getElementById("loginSection").style.display = "none";
        document.getElementById("appSection").style.display = "block";
    } else {
        alert("Invalid login");
    }
}
async function saveEntry() {
    const entry = document.getElementById("diary").value;

    const user_id = localStorage.getItem("user_id")


    const res = await fetch("/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ entry , user_id })
    });

    const data = await res.json();
    console.log(data);
    alert("Mood detected: " + data.mood);
}
async function loadHistory() {
    const user_id = localStorage.getItem("user_id");

    const res = await fetch(`/history/${user_id}`)
    const data = await res.json();

    let html = "";

    data.forEach(item => {
        html += `
<div style="
    background:white;
    padding:15px;
    margin-bottom:10px;
    border-radius:10px;
    box-shadow:0 2px 5px rgba(0,0,0,0.1);
">
    <p><strong>Date: ${item.date}</strong></p>
    <p><strong>Mood: ${item.mood}</strong></p>
    <p>${item.text}</p>
</div>
`;
    });

    document.getElementById("history").innerHTML = html;
}
async function sendMessage() {
    const user_id = localStorage.getItem("user_id");
    const input = document.getElementById("message");
    const message = input.value;

    if (!message) return;

    const chatbox = document.getElementById("chatbox");
    // chatbox.innerHTML += "<p><b>You:</b> " + message + "</p>";

    chatbox.innerHTML += `
<div class="user">
    <div class="bubble">
        <b>You:</b> ${message}
    </div>
</div>
`;

    input.value = "";

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message , user_id })
    });

    const data = await res.json();

    // chatbox.innerHTML += "<p><b>AI:</b> " + data.reply + "</p>";
    chatbox.innerHTML += `
<div class="ai">
    <div class="bubble">
        <b>AI:</b> ${data.reply}<br><br>
        <small>${data.mood}</small>
    </div>
</div>
`;
}

async function loadAnalytics() {
    const user_id = localStorage.getItem("user_id");
    const res = await fetch(`/analytics/${user_id}`);
    const data = await res.json();

    const counts = data.counts;

    // Stats
    let statsHTML = "";

    for (const [emotion, count] of Object.entries(counts)) {
        statsHTML += `<p>${emotion}: ${count}</p>`;
    }

    document.getElementById("stats").innerHTML = statsHTML;

    // Chart

    const ctx = document.getElementById("moodChart");

    const labels = Object.keys(counts);
    const values = Object.values(counts);

    const chartCanvas = document.getElementById("moodChart");

    if (window.moodChartInstance) {
        window.moodChartInstance.destroy();
    }
    window.moodChartInstance = new Chart(ctx, {
        type: "doughnut",

        data: {
            labels: labels,

            datasets: [{
                data: values
            }]
        }
    });
}

loadAnalytics();