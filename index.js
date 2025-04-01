const canvas = document.getElementById("gridCanvas");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

const gridSize = 20;
// const colors = ["#0a192f", "#112240", "#233554", "#64ffda"];
const colors = ["#427d7e", "#194949", "#2c5c5c", "#25645c","#233554","#64ffda"];

let grid = [];

function initializeGrid() {
    grid = [];
    for (let y = canvas.height * 0., row = 0; y < canvas.height; y += gridSize, row++) {
        let rowArray = [];
        for (let x = 0; x < canvas.width * 0.8 - row * gridSize; x += gridSize) {
            rowArray.push({
                x,
                y,
                color: colors[Math.floor(Math.random() * colors.length)]
            });
        }
        grid.push(rowArray);
    }
}

function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    grid.forEach(row => {
        row.forEach(cell => {
            ctx.fillStyle = cell.color;
            ctx.fillRect(cell.x, cell.y, gridSize, gridSize);
        });
    });
}

function updateColors() {
    grid.forEach(row => {
        row.forEach(cell => {
            const currentIndex = colors.indexOf(cell.color);
            cell.color = colors[(currentIndex + 1) % colors.length]; // Smooth color transition
        });
    });
}

function animateGrid() {
    drawGrid();
    updateColors();
    setTimeout(animateGrid, 1000); // Change color smoothly every second
}

// Initialize and start animation
initializeGrid();
animateGrid();


function toggleMenu() {
    document.getElementById("fullscreenMenu").classList.toggle("show");
}

function changeTab(tab) {
    // Update active class
    document.querySelectorAll(".nav-tabs a").forEach(el => el.classList.remove("active"));
    event.target.classList.add("active");

    // Update image based on tab
    const images = {
        "documents": "document.png",
        "tables": "table.png",
        "charts": "chart.png",
        "slides": "slide.png"
    };
    document.getElementById("tabImage").src = images[tab];
}