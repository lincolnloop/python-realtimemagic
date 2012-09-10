realtimeMagic = {
	Client: function(url, send_cookies_insecurely, cookies){
		this.sock = new SockJS(url);

		var client = {
			execute: function(action, payload){
				return this.sock.send(JSON.stringify({action:action, payload:payload}));
			},
			subscribe: function(channel){
				return this.execute("subscribe", channel);
			},
			unsubscribe: function(channel){
				return this.execute("unsubscribe", channel);
			},
			publish: function(channel, message){
				return this.execute("publish", {channel:channel, message:message});
			},
			onmessage: function(){},
			onopen: function(){},
			onclose: function(){},
			send: function(message){
				return this.sock.send(JSON.stringify(message));
			},
			sock: this.sock
		};

		this.sock.onmessage = function(e){
			var message = e.data;
			if ( message.controlMessage ){
				console.log(message);
			}
			else {
				if (client.onmessage) {
					return client.onmessage(message);
				}
			}
		};

		this.sock.onopen = function(){
			if ( send_cookies_insecurely == 'send_cookies_insecurely' ) {
				client.sock.send(JSON.stringify({action:'set_debug_session',
					payload:cookies}));
			}
			if (client.onopen) {
				return client.onopen();
			}
		};

		this.sock.onclose = function(){
			if (client.onclose) {
				return client.onclose();
			}
		};
		return client;

	}

};
