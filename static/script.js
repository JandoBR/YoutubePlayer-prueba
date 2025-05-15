async function updateInfo() {
    try {
        const res = await fetch("/get_info");
        const data = await res.json();
        document.getElementById("song-title").textContent = data.title || "N/A";
        document.getElementById("thumbnail").src = data.thumbnail || "";
    } catch (error) {
        console.error("Error actualizando información:", error);
    }
}


function setStatus(text) {
    document.getElementById("status").textContent = text;
    updateInfo();
}

async function changeVolume() {
    const level = prompt("Ingresa el volumen (0 a 100):");
    if (level !== null) {
        await fetch("/set_volume", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level: parseFloat(level) })
        });
        setStatus("🔊 Volumen cambiado");
    }
}

async function changeTime() {
    const time = prompt("Segundos a avanzar:");
    if (time !== null) {
        await fetch("/set_time_song", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ time: parseInt(time) })
        });
        setStatus("⏳ Tiempo actualizado");
    }
}

async function shuffle() {
    await fetch("/shuffle", { method: "POST" });
    setStatus("🔀 Playlist mezclada");
}

async function playByIndex() {
    const index = prompt("Índice de la canción:");
    if (index !== null) {
        await fetch("/play_index_song", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index: parseInt(index) })
        });
        setStatus("🎲 Canción seleccionada");
    }
}

async function pause() {
    const res = await fetch("/pause", { method: "POST" });
    const data = await res.json();
    setStatus(data.status || data.error);
}

async function resume() {
    const res = await fetch("/resume", { method: "POST" });
    const data = await res.json();
    setStatus(data.status || data.error);
}

async function nextSong() {
    const res = await fetch("/next", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: 0 })
    });
    const data = await res.json();
    setStatus("⏭️ " + (data.title || data.status));
    updateInfo();
}

async function previousSong() {
    const res = await fetch("/previous", { method: "POST" });
    const data = await res.json();
    setStatus("⏮️ " + (data.title || data.status));
}

async function shutdown() {
    // Mostrar mensaje de "Servidor apagado"
    document.body.innerHTML = "<h1>🛑 Servidor apagado</h1><p>La página se cerrará pronto...</p>";

    // Esperar medio segundo
    await new Promise(resolve => setTimeout(resolve, 500));

    // Apagar el servidor
    await fetch("/shutdown", { method: "POST" });


}



window.onload = async () => {
    fetch("/playstart", { method: "POST" });

    // Espera 1 segundo para asegurarte de que la canción comenzó
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Primera actualización
    await updateInfo();
};
