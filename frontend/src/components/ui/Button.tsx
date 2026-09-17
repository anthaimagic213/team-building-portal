import { ButtonHTMLAttributes, forwardRef } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { variant?: Variant; loading?: boolean; }
const styles: Record<Variant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700', secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  danger: 'bg-red-600 text-white hover:bg-red-700', ghost: 'text-slate-600 hover:bg-slate-100',
};
const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ variant = 'primary', loading, disabled, children, className = '', ...props }, ref) => (
  <button ref={ref} disabled={disabled || loading} className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`} {...props}>
    {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />}{children}
  </button>
));
Button.displayName = 'Button';
export default Button;