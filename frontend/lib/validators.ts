/** Convenience validation only - the Django backend re-validates everything. */
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

export interface TicketFormValues {
  title: string;
  description: string;
  category: string;
  building: string;
  floor: string;
  room_or_area: string;
}
export type FormErrors<T extends string = string> = Partial<Record<T, string>>;

export function validateTicketForm(v: TicketFormValues): FormErrors {
  const errors: FormErrors = {};
  if (!v.title.trim()) errors.title = "Enter a short title.";
  else if (v.title.trim().length > 200) errors.title = "Title must be 200 characters or fewer.";
  if (!v.description.trim()) errors.description = "Describe the problem.";
  else if (v.description.trim().length > 5000) errors.description = "Description is too long (max 5000 characters).";
  if (!v.category) errors.category = "Select a category.";
  if (!v.building.trim()) errors.building = "Enter the building or block.";
  if (v.floor.length > 20) errors.floor = "Floor must be 20 characters or fewer.";
  if (v.room_or_area.length > 100) errors.room_or_area = "Room/area must be 100 characters or fewer.";
  return errors;
}

export function validateImage(file: File | null | undefined): string | null {
  if (!file) return null;
  if (!IMAGE_TYPES.includes(file.type)) return "Choose a JPEG, PNG, WEBP or GIF image.";
  if (file.size > MAX_IMAGE_BYTES) return `Image is too large (maximum ${MAX_IMAGE_BYTES / 1024 / 1024} MB).`;
  return null;
}

export function validateLogin(email: string, password: string): FormErrors<"email" | "password"> {
  const errors: FormErrors<"email" | "password"> = {};
  if (!email.trim()) errors.email = "Enter your email address.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) errors.email = "Enter a valid email address.";
  if (!password) errors.password = "Enter your password.";
  return errors;
}

export function validateRequiredNote(note: string, what: string): string | null {
  return note.trim() ? null : `${what} is required.`;
}
