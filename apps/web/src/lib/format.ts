export function formatDecimal(value: string): string {
  const number = Number(value);
  if (Number.isNaN(number)) return value;
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 8 }).format(
    number,
  );
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(value));
}
