"use client";

export default function DeleteSignalButton() {
  return (
    <button
      type="submit"
      onClick={(event) => {
        if (!confirm("Apagar este sinal? Essa ação não pode ser desfeita.")) {
          event.preventDefault();
        }
      }}
      className="text-sm text-red-600 hover:underline dark:text-red-400"
    >
      Apagar
    </button>
  );
}
