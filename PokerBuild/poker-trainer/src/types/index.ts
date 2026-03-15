/**
 * Poker Therapist Suite - Type Definitions
 */

/**
 * Represents a playing card
 */
export interface Card {
  suit: 'hearts' | 'diamonds' | 'clubs' | 'spades'
  rank: '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10' | 'J' | 'Q' | 'K' | 'A'
}

/**
 * Represents a poker hand
 */
export interface PokerHand {
  id: string
  cards: Card[]
  description: string
}

/**
 * Represents a training session
 */
export interface TrainingSession {
  id: string
  name: string
  description: string
  createdAt: Date
  updatedAt: Date
}

/**
 * Application state
 */
export interface AppState {
  currentSession: TrainingSession | null
  isLoading: boolean
  error: string | null
}
