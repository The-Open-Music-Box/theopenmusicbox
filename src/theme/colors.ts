/**
 * Application Color Theme
 *
 * This file centralizes color definitions used throughout the application.
 * Use these variables instead of hardcoded Tailwind classes to maintain consistency.
 */

export const colors = {
  primary: {
    main: 'indigo-600',
    hover: 'indigo-500',
    light: 'indigo-100',
    dark: 'indigo-700',
  },
  secondary: {
    main: 'cyan-500',
    hover: 'cyan-400',
    light: 'cyan-100',
    dark: 'cyan-600',
  },
  error: {
    main: 'red-600',
    hover: 'red-500',
    light: 'red-100',
    background: 'red-100',
    border: 'red-400',
    text: 'red-700',
  },
  success: {
    main: 'green-600',
    hover: 'green-500',
    light: 'green-100',
  },
  warning: {
    main: 'yellow-500',
    light: 'yellow-100',
  },
  text: {
    primary: 'gray-900',
    secondary: 'gray-600',
    disabled: 'gray-400',
    light: 'gray-300',
    white: 'white',
  },
  background: {
    main: 'white',
    dark: 'gray-800',
    light: 'gray-50',
    medium: 'gray-200',
  },
  border: {
    main: 'gray-300',
    dark: 'gray-700',
    light: 'gray-200',
  },
};
