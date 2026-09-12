import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../../components/auth/AuthProvider';

function TestComponent() {
  const { isAuthenticated, user, isAuthLoaded, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="loaded">{isAuthLoaded.toString()}</div>
      <div data-testid="auth">{isAuthenticated.toString()}</div>
      <div data-testid="user">{user?.email || 'none'}</div>
      <button onClick={() => login({ id: '1', email: 'test@test.com', username: 'test' })}>
        Login
      </button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('initializes with no auth', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(await screen.findByTestId('loaded')).toHaveTextContent('true');
    expect(screen.getByTestId('auth')).toHaveTextContent('false');
    expect(screen.getByTestId('user')).toHaveTextContent('none');
  });

  it('can login and logout', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText('Login').click();
    });

    expect(screen.getByTestId('auth')).toHaveTextContent('true');
    expect(screen.getByTestId('user')).toHaveTextContent('test@test.com');

    await act(async () => {
      screen.getByText('Logout').click();
    });

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('false'));

    expect(screen.getByTestId('auth')).toHaveTextContent('false');
    expect(screen.getByTestId('user')).toHaveTextContent('none');
  });

  it('restores auth from session if token is present', async () => {
    // Mock the fetch call to return a user session
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: '2', email: 'restored@test.com', username: 'restored' }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for the async useEffect to complete
    await waitFor(() => {
      expect(screen.getByTestId('auth')).toHaveTextContent('true');
      expect(screen.getByTestId('user')).toHaveTextContent('restored@test.com');
    });

    // Restore fetch
    (global.fetch as jest.Mock).mockRestore();
  });
});
