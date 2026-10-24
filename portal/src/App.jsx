import { useEffect, useState } from "react";

// Carné: solo dígitos, de 7 a 10 (ej. 1102124). Ajustar si R1 define otro formato en la API.
const FORMATO_CARNE = /^\d{7,10}$/;

// Portal mínimo (caso de uso 1): elegir curso, asignarse y ver el resultado.
export default function App() {
  const [cursos, setCursos] = useState([]);
  const [errorCursos, setErrorCursos] = useState(false);
  const [estudiante, setEstudiante] = useState("");
  const [mensaje, setMensaje] = useState(null);
  const [enviando, setEnviando] = useState(false);

  // Si la API falla o no devuelve una lista, se avisa en vez de dejar la tabla vacía.
  const cargarCursos = () =>
    fetch("/api/cursos")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((lista) => {
        if (!Array.isArray(lista)) throw new Error();
        setCursos(lista);
        setErrorCursos(false);
      })
      .catch(() => {
        setCursos([]);
        setErrorCursos(true);
      });

  useEffect(() => {
    cargarCursos();
  }, []);

  async function asignar(cursoId) {
    const carne = estudiante.trim();
    if (!carne) {
      setMensaje({ tipo: "error", texto: "Ingrese su carné" });
      return;
    }
    if (!FORMATO_CARNE.test(carne)) {
      setMensaje({ tipo: "error", texto: "El carné debe tener de 7 a 10 dígitos, sin letras ni espacios" });
      return;
    }
    setEnviando(true);
    try {
      const r = await fetch("/api/asignaciones", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estudiante_id: carne, curso_id: cursoId }),
      });
      // Un 502/504 de Nginx trae HTML, no JSON: no es "sin conexión", es un error del servidor.
      const cuerpo = await r.json().catch(() => ({}));
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
        <input
          value={estudiante}
          onChange={(e) => setEstudiante(e.target.value)}
          placeholder="1102124"
          inputMode="numeric"
          maxLength={10}
        />
      </label>
      {mensaje && (
        <p role="status" style={{ color: colores[mensaje.tipo], fontWeight: 600 }}>
          {mensaje.texto}
        </p>
      )}
      {errorCursos && (
        <p role="alert" style={{ color: colores.error }}>
          No se pudo cargar la lista de cursos.{" "}
          <button onClick={cargarCursos}>Reintentar</button>
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
