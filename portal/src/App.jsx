import { useEffect, useState } from "react";

// Portal mínimo (caso de uso 1): elegir curso, asignarse y ver el resultado.
export default function App() {
  const [cursos, setCursos] = useState([]);
  const [estudiante, setEstudiante] = useState("");
  const [mensaje, setMensaje] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const cargarCursos = () =>
    fetch("/api/cursos").then((r) => r.json()).then(setCursos).catch(() => setCursos([]));

  useEffect(() => {
    cargarCursos();
  }, []);

  async function asignar(cursoId) {
    if (!estudiante.trim()) {
      setMensaje({ tipo: "error", texto: "Ingrese su carné" });
      return;
    }
    setEnviando(true);
    try {
      const r = await fetch("/api/asignaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estudiante_id: estudiante.trim(), curso_id: cursoId }),
      });
      const cuerpo = await r.json();
      if (r.status === 201) {
        setMensaje({ tipo: "ok", texto: `${cuerpo.detalle}. Cupos restantes: ${cuerpo.cupos_restantes}` });
      } else if (r.status === 409) {
        setMensaje({ tipo: "lleno", texto: cuerpo.detalle });
      } else {
        setMensaje({ tipo: "error", texto: cuerpo.detalle ?? "No se pudo procesar la solicitud" });
      }
    } catch {
      setMensaje({ tipo: "error", texto: "Sin conexión con el servidor" });
    } finally {
      setEnviando(false);
      cargarCursos();
    }
  }

  const colores = { ok: "#1b7f3b", lleno: "#a15c00", error: "#b00020" };

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 640, margin: "40px auto", padding: "0 16px" }}>
      <h1>Asignación de cursos</h1>
      <label>
        Carné:{" "}
        <input value={estudiante} onChange={(e) => setEstudiante(e.target.value)} placeholder="1102124" />
      </label>
      {mensaje && (
        <p role="status" style={{ color: colores[mensaje.tipo], fontWeight: 600 }}>
          {mensaje.texto}
        </p>
      )}
      <table style={{ width: "100%", marginTop: 16, borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Curso</th>
            <th align="right">Cupos</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {cursos.map((c) => (
            <tr key={c.id}>
              <td>{c.codigo} · {c.nombre}</td>
              <td align="right">{c.cupos}</td>
              <td align="right">
                <button disabled={enviando} onClick={() => asignar(c.id)}>Asignar curso</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
