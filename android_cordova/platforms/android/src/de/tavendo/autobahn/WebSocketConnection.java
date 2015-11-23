/******************************************************************************
 *
 *  Copyright 2011-2012 Tavendo GmbH
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 ******************************************************************************/

package de.tavendo.autobahn;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.net.Socket;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.cert.Certificate;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;

import javax.net.SocketFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManagerFactory;

import android.net.SSLCertificateSocketFactory;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.util.Log;
import de.tavendo.autobahn.WebSocket.WebSocketConnectionObserver.WebSocketCloseNotification;
import de.tavendo.autobahn.WebSocketMessage.WebSocketCloseCode;

public class WebSocketConnection implements WebSocket {
	private static final String TAG = "websocketssl";
	private static final String WS_URI_SCHEME = "ws";
	private static final String WSS_URI_SCHEME = "wss";
	private static final String WS_WRITER = "WebSocketWriter";
	private static final String WS_READER = "WebSocketReader";

	private final Handler mHandler;

	private WebSocketReader mWebSocketReader;
	private WebSocketWriter mWebSocketWriter;

	private Socket mSocket;
	private SocketThread mSocketThread;

	private URI mWebSocketURI;
	private String[] mWebSocketSubprotocols;

	private WeakReference<WebSocketConnectionObserver> mWebSocketConnectionObserver;

	private WebSocketOptions mWebSocketOptions;
	private boolean mPreviousConnection = false;



	public WebSocketConnection() {
		Log.d(TAG, "WebSocket connection created.");

		this.mHandler = new ThreadHandler(this);
	}



	//
	// Forward to the writer thread
	public void sendTextMessage(String payload) {
		mWebSocketWriter.forward(new WebSocketMessage.TextMessage(payload));
	}


	public void sendRawTextMessage(byte[] payload) {
		mWebSocketWriter.forward(new WebSocketMessage.RawTextMessage(payload));
	}


	public void sendBinaryMessage(byte[] payload) {
		mWebSocketWriter.forward(new WebSocketMessage.BinaryMessage(payload));
	}



	public boolean isConnected() {
		return mSocket != null && mSocket.isConnected() && !mSocket.isClosed();
	}



	private void failConnection(WebSocketCloseNotification code, String reason) {
		Log.d(TAG, "fail connection [code = " + code + ", reason = " + reason);

		if (mWebSocketReader != null) {
			mWebSocketReader.quit();

			try {
				mWebSocketReader.join();
			} catch (InterruptedException e) {
				e.printStackTrace();
			}
		} else {
			Log.d(TAG, "mReader already NULL");
		}

		if (mWebSocketWriter != null) {
			mWebSocketWriter.forward(new WebSocketMessage.Quit());

			try {
				mWebSocketWriter.join();
			} catch (InterruptedException e) {
				e.printStackTrace();
			}
		} else {
			Log.d(TAG, "mWriter already NULL");
		}

		if (mSocket != null) {
			mSocketThread.getHandler().post(new Runnable() {

				@Override
				public void run() {
					mSocketThread.stopConnection();
				}
			});
		} else {
			Log.d(TAG, "mTransportChannel already NULL");
		}
		
		mSocketThread.getHandler().post(new Runnable() {
			
			@Override
			public void run() {
				Looper.myLooper().quit();
			}
		});

		onClose(code, reason);

		Log.d(TAG, "worker threads stopped");
	}



	public void connect(URI webSocketURI, WebSocketConnectionObserver connectionObserver) throws WebSocketException {
		connect(webSocketURI, connectionObserver, new WebSocketOptions());
	}

	public void connect(URI webSocketURI, WebSocketConnectionObserver connectionObserver, WebSocketOptions options) throws WebSocketException {
		connect(webSocketURI, null, connectionObserver, options);
	}

	public void connect(URI webSocketURI, String[] subprotocols, WebSocketConnectionObserver connectionObserver, WebSocketOptions options) throws WebSocketException {
		if (isConnected()) {
			throw new WebSocketException("already connected");
		}

		if (webSocketURI == null) {
			throw new WebSocketException("WebSockets URI null.");
		} else {
			this.mWebSocketURI = webSocketURI;
			if (!mWebSocketURI.getScheme().equals(WS_URI_SCHEME) && !mWebSocketURI.getScheme().equals(WSS_URI_SCHEME)) {
				throw new WebSocketException("unsupported scheme for WebSockets URI");
			}

			this.mWebSocketSubprotocols = subprotocols;
			this.mWebSocketConnectionObserver = new WeakReference<WebSocketConnectionObserver>(connectionObserver);
			this.mWebSocketOptions = new WebSocketOptions(options);

			connect();
		}
	}

	public void disconnect() {
        Log.d(TAG, "disconnect");
		if (mWebSocketWriter != null && mWebSocketWriter.isAlive()) {
			mWebSocketWriter.forward(new WebSocketMessage.Close());
		} else {
			Log.d(TAG, "Could not send WebSocket Close .. writer already null");
		}

		this.mPreviousConnection = false;
	}

	/**
	 * Reconnect to the server with the latest options 
	 * @return true if reconnection performed
	 */
	public boolean reconnect() {
		if (!isConnected() && (mWebSocketURI != null)) {
			connect();
			return true;
		}
		return false;
	}

	private void connect() {
		mSocketThread = new SocketThread(mWebSocketURI, mWebSocketOptions);

		mSocketThread.start();
		synchronized (mSocketThread) {
			try {
				mSocketThread.wait();
			} catch (InterruptedException e) {
			}
		}
		mSocketThread.getHandler().post(new Runnable() {
			
			@Override
			public void run() {
				mSocketThread.startConnection();
			}
		});
		
		synchronized (mSocketThread) {
			try {
				mSocketThread.wait();
			} catch (InterruptedException e) {
			}
		}

        Log.d(TAG, "Get Socket");
		this.mSocket = mSocketThread.getSocket();
		
		if (mSocket == null) {
            Log.d(TAG, "Socket Null");
			onClose(WebSocketCloseNotification.CANNOT_CONNECT, mSocketThread.getFailureMessage());
		} else if (mSocket.isConnected()) {
            Log.d(TAG, "Socket Connected");
			try {
				createReader();
				createWriter();

				WebSocketMessage.ClientHandshake clientHandshake = new WebSocketMessage.ClientHandshake(mWebSocketURI, null, mWebSocketSubprotocols);
				mWebSocketWriter.forward(clientHandshake);
			} catch (Exception e) {
				onClose(WebSocketCloseNotification.INTERNAL_ERROR, e.getLocalizedMessage());
			}
		} else {
			onClose(WebSocketCloseNotification.CANNOT_CONNECT, "could not connect to WebSockets server");
		}
	}

	/**
	 * Perform reconnection
	 * 
	 * @return true if reconnection was scheduled
	 */
	protected boolean scheduleReconnect() {
		/**
		 * Reconnect only if:
		 *  - connection active (connected but not disconnected)
		 *  - has previous success connections
		 *  - reconnect interval is set
		 */
		int interval = mWebSocketOptions.getReconnectInterval();
        boolean shouldReconnect = mSocket != null
                && mSocket.isConnected()
                && mPreviousConnection
                && (interval > 0);
        if (shouldReconnect) {
			Log.d(TAG, "WebSocket reconnection scheduled");
			mHandler.postDelayed(new Runnable() {

				public void run() {
					Log.d(TAG, "WebSocket reconnecting...");
					reconnect();
				}
			}, interval);
		}
		return shouldReconnect;
	}

	/**
	 * Common close handler
	 * 
	 * @param code       Close code.
	 * @param reason     Close reason (human-readable).
	 */
	private void onClose(WebSocketCloseNotification code, String reason) {
		boolean reconnecting = false;

		if ((code == WebSocketCloseNotification.CANNOT_CONNECT) || (code == WebSocketCloseNotification.CONNECTION_LOST)) {
			reconnecting = scheduleReconnect();
		}

		WebSocketConnectionObserver webSocketObserver = mWebSocketConnectionObserver.get();
		if (webSocketObserver != null) {
			try {
				if (reconnecting) {
					webSocketObserver.onClose(WebSocketCloseNotification.RECONNECT, reason);
				} else {
					webSocketObserver.onClose(code, reason);
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		} else {
			Log.d(TAG, "WebSocketObserver null");
		}
	}




	protected void processAppMessage(Object message) {
	}


	/**
	 * Create WebSockets background writer.
	 */
	protected void createWriter() {
		mWebSocketWriter = new WebSocketWriter(mHandler, mSocket, mWebSocketOptions, WS_WRITER);
		mWebSocketWriter.start();

		synchronized (mWebSocketWriter) {
			try {
				mWebSocketWriter.wait();
			} catch (InterruptedException e) {
			}
		}

		Log.d(TAG, "WebSocket writer created and started.");
	}


	/**
	 * Create WebSockets background reader.
	 */
	protected void createReader() {

		mWebSocketReader = new WebSocketReader(mHandler, mSocket, mWebSocketOptions, WS_READER);
		mWebSocketReader.start();

		synchronized (mWebSocketReader) {
			try {
				mWebSocketReader.wait();
			} catch (InterruptedException e) {
			}
		}

		Log.d(TAG, "WebSocket reader created and started.");
	}

	private void handleMessage(Message message) {
		WebSocketConnectionObserver webSocketObserver = mWebSocketConnectionObserver.get();

		if (message.obj instanceof WebSocketMessage.TextMessage) {
			WebSocketMessage.TextMessage textMessage = (WebSocketMessage.TextMessage) message.obj;

			if (webSocketObserver != null) {
				webSocketObserver.onTextMessage(textMessage.mPayload);
			} else {
				Log.d(TAG, "could not call onTextMessage() .. handler already NULL");
			}

		} else if (message.obj instanceof WebSocketMessage.RawTextMessage) {
			WebSocketMessage.RawTextMessage rawTextMessage = (WebSocketMessage.RawTextMessage) message.obj;

			if (webSocketObserver != null) {
				webSocketObserver.onRawTextMessage(rawTextMessage.mPayload);
			} else {
				Log.d(TAG, "could not call onRawTextMessage() .. handler already NULL");
			}

		} else if (message.obj instanceof WebSocketMessage.BinaryMessage) {
			WebSocketMessage.BinaryMessage binaryMessage = (WebSocketMessage.BinaryMessage) message.obj;

			if (webSocketObserver != null) {
				webSocketObserver.onBinaryMessage(binaryMessage.mPayload);
			} else {
				Log.d(TAG, "could not call onBinaryMessage() .. handler already NULL");
			}

		} else if (message.obj instanceof WebSocketMessage.Ping) {
			WebSocketMessage.Ping ping = (WebSocketMessage.Ping) message.obj;
			Log.d(TAG, "WebSockets Ping received");

			WebSocketMessage.Pong pong = new WebSocketMessage.Pong();
			pong.mPayload = ping.mPayload;
			mWebSocketWriter.forward(pong);

		} else if (message.obj instanceof WebSocketMessage.Pong) {
			WebSocketMessage.Pong pong = (WebSocketMessage.Pong) message.obj;

			Log.d(TAG, "WebSockets Pong received" + pong.mPayload);

		} else if (message.obj instanceof WebSocketMessage.Close) {
			WebSocketMessage.Close close = (WebSocketMessage.Close) message.obj;

			Log.d(TAG, "WebSockets Close received (" + close.getCode() + " - " + close.getReason() + ")");

			mWebSocketWriter.forward(new WebSocketMessage.Close(WebSocketCloseCode.NORMAL));

		} else if (message.obj instanceof WebSocketMessage.ServerHandshake) {
			WebSocketMessage.ServerHandshake serverHandshake = (WebSocketMessage.ServerHandshake) message.obj;

			Log.d(TAG, "opening handshake received");

			if (serverHandshake.mSuccess) {
				if (webSocketObserver != null) {
					webSocketObserver.onOpen();
				} else {
					Log.d(TAG, "could not call onOpen() .. handler already NULL");
				}
				mPreviousConnection = true;
			}

		} else if (message.obj instanceof WebSocketMessage.ConnectionLost) {
			//			WebSocketMessage.ConnectionLost connectionLost = (WebSocketMessage.ConnectionLost) message.obj;
			failConnection(WebSocketCloseNotification.CONNECTION_LOST, "WebSockets connection lost");

		} else if (message.obj instanceof WebSocketMessage.ProtocolViolation) {
			//			WebSocketMessage.ProtocolViolation protocolViolation = (WebSocketMessage.ProtocolViolation) message.obj;
			failConnection(WebSocketCloseNotification.PROTOCOL_ERROR, "WebSockets protocol violation");

		} else if (message.obj instanceof WebSocketMessage.Error) {
			WebSocketMessage.Error error = (WebSocketMessage.Error) message.obj;
			failConnection(WebSocketCloseNotification.INTERNAL_ERROR, "WebSockets internal error (" + error.mException.toString() + ")");

		} else if (message.obj instanceof WebSocketMessage.ServerError) {
			WebSocketMessage.ServerError error = (WebSocketMessage.ServerError) message.obj;
			failConnection(WebSocketCloseNotification.SERVER_ERROR, "Server error " + error.mStatusCode + " (" + error.mStatusMessage + ")");

		} else {
			processAppMessage(message.obj);

		}
	}



	public static class SocketThread extends Thread {
		private static final String WS_CONNECTOR = "WebSocketConnector";

		private final URI mWebSocketURI;

		private Socket mSocket = null;
		private String mFailureMessage = null;
		
		private Handler mHandler;
		


		public SocketThread(URI uri, WebSocketOptions options) {
			this.setName(WS_CONNECTOR);
			
			this.mWebSocketURI = uri;
		}



		@Override
		public void run() {
			Looper.prepare();
			this.mHandler = new Handler();
			synchronized (this) {
				notifyAll();
			}
			
			Looper.loop();
			Log.d(TAG, "SocketThread exited.");
		}



		public void startConnection() {	
			try {
				String host = mWebSocketURI.getHost();
				int port = mWebSocketURI.getPort();

				if (port == -1) {
					if (mWebSocketURI.getScheme().equals(WSS_URI_SCHEME)) {
						port = 443;
					} else {
						port = 80;
					}
				}
				
				SocketFactory factory = null;
				/*if (mWebSocketURI.getScheme().equalsIgnoreCase(WSS_URI_SCHEME)) {
					// HERE FIND ME TODO
					try {
						CertificateFactory cf = CertificateFactory.getInstance("X.509");
						// From https://www.washington.edu/itconnect/security/ca/load-der.crt
						String cert = "" +
								"-----BEGIN CERTIFICATE-----\n" +
								"MIIDaTCCAlGgAwIBAgIJAKllPSHSsRZ1MA0GCSqGSIb3DQEBBQUAMEsxCzAJBgNV\n" +
								"BAYTAlVTMQswCQYDVQQIDAJUWDEMMAoGA1UEBwwDSE9VMSEwHwYDVQQKDBhJbnRl\n" +
								"cm5ldCBXaWRnaXRzIFB0eSBMdGQwHhcNMTUwNDA2MjA0MjI0WhcNMTYwNDA1MjA0\n" +
								"MjI0WjBLMQswCQYDVQQGEwJVUzELMAkGA1UECAwCVFgxDDAKBgNVBAcMA0hPVTEh\n" +
								"MB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0B\n" +
								"AQEFAAOCAQ8AMIIBCgKCAQEAnjmwS4R4+TUNbAakEo4wgXny8fjDfWRhjTo3wojt\n" +
								"nLrD2RwSGPEsykHkJkDF8AFlpZZsOR0mqJF6w5DJx6dextCPF26D3uM+xcLNtCum\n" +
								"ml2OL1JMVQRI1DdESJamNyYTHo7Di4VzA9kd7EpVKsqEi0xmb0rv2kFPdVpXcn9t\n" +
								"BbcAh3uhZClos71MnWssOBnKTSDqgduu5vUm29hr9C2b5vWs2uXDHJ7X6RhdQnQ3\n" +
								"pkNTq7P4++xfV7kyXYWpe3FyeS1aNt5HUASx5eb1cPzxEcW7BDCgpCC4z6woPFMy\n" +
								"8zcwCSCbNQsH2k6Xc1i1C3q+7szIAsKVUh0Em0l86+9JbwIDAQABo1AwTjAdBgNV\n" +
								"HQ4EFgQU0JLqGGEPyL0oTTnQ7U/gPvkod5swHwYDVR0jBBgwFoAU0JLqGGEPyL0o\n" +
								"TTnQ7U/gPvkod5swDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAeup2\n" +
								"U0vG0j1JLfB9oMBh7WjfXPzkmVmh4jS7AcdObgCU8AR4XyQn/OEQzKLIsSIZEHQa\n" +
								"cUSyHRnlm2I7A3pLDsUw0tseVe3iDvSyKDlEJarJpZJTwzt3tI5KrT/EVGnfZ95j\n" +
								"RXU/bwMFVZBVU+4x+jWCDPt+9jKQyIV9TQ9IZkV1EbQeuPXbGpBSt7rFduKNwP30\n" +
								"R1gTyny6N27yrTc4N+aaoenbcTMTJSGS7bH2MS76QO7rT40ZCIMcPhQ4t5iQ/N06\n" +
								"DFxawSxUq/IqBRJCJ9vb9vo6iFv0lhb2N9N05970AlzDhxjE04AsV/uo1RYZqd+h\n" +
								"r/esTH4fLryUh3Pwpw==\n" +
								"-----END CERTIFICATE-----\n";
						InputStream caInput = new ByteArrayInputStream(cert.getBytes(StandardCharsets.UTF_8));

						Certificate ca;
						try {
							ca = cf.generateCertificate(caInput);
							System.out.println("ca=" + ((X509Certificate) ca).getSubjectDN());
						} finally {
							caInput.close();
						}

						// Create a KeyStore containing our trusted CAs
						String keyStoreType = KeyStore.getDefaultType();
						KeyStore keyStore = KeyStore.getInstance(keyStoreType);
						keyStore.load(null, null);
						keyStore.setCertificateEntry("ca", ca);

						// Create a TrustManager that trusts the CAs in our KeyStore
						String tmfAlgorithm = TrustManagerFactory.getDefaultAlgorithm();
						TrustManagerFactory tmf = TrustManagerFactory.getInstance(tmfAlgorithm);
						tmf.init(keyStore);

						// Create an SSLContext that uses our TrustManager
						SSLContext context = SSLContext.getInstance("TLS");
						context.init(null, tmf.getTrustManagers(), null);
						factory = context.getSocketFactory();
					} catch (Exception e){
						Log.i("websocket",e.toString());
					}
				} else {
					factory = SocketFactory.getDefault();
				}*/

                factory = SocketFactory.getDefault();
				// Do not replace host string with InetAddress or you lose automatic host name verification
                Log.d(TAG, "Create socket.");
				this.mSocket = factory.createSocket(host, port);
			} catch (IOException e) {
                Log.d(TAG, "Create socket EXCEPTION");
                Log.d(TAG, e.toString());
				this.mFailureMessage = e.getLocalizedMessage();
			}
			
			synchronized (this) {
				notifyAll();
			}
            Log.d(TAG, "Leaving start_connection");
		}
		
		public void stopConnection() {
			try {
				mSocket.close();
				this.mSocket = null;
			} catch (IOException e) {
				this.mFailureMessage = e.getLocalizedMessage();
			}
		}

		public Handler getHandler() {
			return mHandler;
		}
		public Socket getSocket() {
			return mSocket;
		}
		public String getFailureMessage() {
			return mFailureMessage;
		}
	}



	private static class ThreadHandler extends Handler {
		private final WeakReference<WebSocketConnection> mWebSocketConnection;



		public ThreadHandler(WebSocketConnection webSocketConnection) {
			super();

			this.mWebSocketConnection = new WeakReference<WebSocketConnection>(webSocketConnection);
		}



		@Override
		public void handleMessage(Message message) {
			WebSocketConnection webSocketConnection = mWebSocketConnection.get();
			if (webSocketConnection != null) {
				webSocketConnection.handleMessage(message);
			}
		}
	}
}
