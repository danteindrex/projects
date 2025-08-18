import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatInterface from '../ChatInterface'

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}

Object.defineProperty(global, 'WebSocket', {
  writable: true,
  value: jest.fn(() => mockWebSocket),
})

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders chat interface', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText('AI Assistant Chat')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask me about your business systems...')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('shows welcome message', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText(/Hello! I'm your AI assistant/)).toBeInTheDocument()
  })

  it('sends message when form is submitted', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    const button = screen.getByRole('button')
    
    await user.type(input, 'Test message')
    await user.click(button)
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    
    await user.type(input, 'Test message{enter}')
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('disables input and button when loading', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    const button = screen.getByRole('button')
    
    await user.type(input, 'Test message')
    await user.click(button)
    
    await waitFor(() => {
      expect(input).toBeDisabled()
      expect(button).toBeDisabled()
    })
  })

  it('shows connection status', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText('Connected')).toBeInTheDocument()
  })

  it('simulates tool calling for Jira queries', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    
    await user.type(input, 'Show me Jira issues{enter}')
    
    await waitFor(() => {
      expect(screen.getByText(/jira_api executed successfully/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('simulates tool calling for Zendesk queries', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    
    await user.type(input, 'Show me Zendesk tickets{enter}')
    
    await waitFor(() => {
      expect(screen.getByText(/zendesk_api executed successfully/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('clears input after sending message', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('Ask me about your business systems...')
    
    await user.type(input, 'Test message')
    await user.click(screen.getByRole('button'))
    
    expect(input).toHaveValue('')
  })

  it('prevents sending empty messages', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const button = screen.getByRole('button')
    
    await user.click(button)
    
    // Should not add any new messages beyond the welcome message
    const messages = screen.getAllByText(/Hello! I'm your AI assistant/)
    expect(messages).toHaveLength(1)
  })
})