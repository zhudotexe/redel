export function sorted<T>(arr: Iterable<T> | T[], compareFn?: (a: T, b: T) => number): T[] {
  return [...arr].sort(compareFn);
}
