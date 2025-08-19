/**
 * Event Bus Service
 *
 * Provides a simple event-based communication mechanism between Vue components
 * without creating direct dependencies.
 */

import { reactive } from 'vue';

type EventListener = (...args: unknown[]) => void;
interface EventCallbacks {
  [event: string]: EventListener[];
}

export const eventBus = reactive({
  events: {} as EventCallbacks,
  
  /**
   * Register an event listener
   * @param event - Name of the event to listen for
   * @param callback - Function to call when the event is emitted
   */
  on(event: string, callback: EventListener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  },
  
  /**
   * Remove an event listener
   * @param event - Name of the event
   * @param callback - Function to remove (if omitted, all listeners for the event are removed)
   */
  off(event: string, callback?: EventListener) {
    if (!this.events[event]) return;
    if (!callback) {
      this.events[event] = [];
      return;
    }
    this.events[event] = this.events[event].filter(cb => cb !== callback);
  },
  
  /**
   * Emit an event with the specified arguments
   * @param event - Name of the event to emit
   * @param args - Arguments to pass to listeners
   */
  emit(event: string, ...args: unknown[]) {
    if (!this.events[event]) return;
    this.events[event].forEach(callback => {
      callback(...args);
    });
  }
});
