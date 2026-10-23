import { useEffect, useState } from "react";

// Pantalla inicial: solo comprueba que el portal llega a la API.
export default function App() {
  const [estado, setEstado] = useState("Comprobando conexión con la API...");

  useEffect(() => {
    fetch("/api/salud")
      .then((r) => r.json())
      .then((s) => setEstado(`API: ${s.api} · Base de datos: ${s.base_de_datos}`))
      .catch(() => setEstado("Sin conexión con la API"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 640, margin: "40px auto", padding: "0 16px" }}>
      <h1>Portal de Asignaciones</h1>
      <p>{estado}</p>
    </main>
  );
}
