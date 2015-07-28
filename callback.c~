/***********************************************************
* IOT Project
* Logic for Running Callback function from Parse
* Written from Scratch

Parent Thread --> Runs Camera Logic
Thread 1 	  --> Runs Push Notification Service to handle Pushes from Parse
***********************************************************/

#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <parse.h>
#include <pthread.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <errno.h>

//Mer cermperler derercterves
#define PORT_CALLBACK 50008
#define MAXPENDING 5    /* Maximum outstanding connection requests */
#define HOST "127.0.0.1"

char dataUUID[] = "bb946c14-758a-4448-8b78-69b04ba1bb8b";
char copied_string[] = "{result\":\"1111111111\"}";

//@TODO: IMPORT THREADING INFO
// This is lock needed to ensure proper synchronization while updating some data of lightBulb struct
pthread_mutex_t lock;

//callback function to retrieve object identifier
/*void myCloudFunctionCallback(ParseClient client, int error, int httpStatus, const char* httpResponseBody) {
	if (error == 0 && httpResponseBody != NULL) {
       		// httpResponseBody holds the Cloud Function response
		printf("Object ID full response: %s\n", httpResponseBody);
		strcpy(copied_string, httpResponseBody);//, sizeof(copied_string) - 1);
	}else{
		//object.ID = NULL;
	}
}*/




//Function that returns a socket descriptor
int createServerSocket(int port)
{
	int servSock;
    	struct sockaddr_in servAddr;
	if ((servSock = socket(PF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0)
	{
		printf("callback::createServerSocket(): ERROR: Cannot open Server Socket\n");
	}

	/* Construct local address structure */
	memset(&servAddr, 0, sizeof(servAddr));       /* Zero out structure */
	servAddr.sin_family = AF_INET;                /* Internet address family */
	servAddr.sin_addr.s_addr = htonl(INADDR_ANY); /* Any incoming interface */
	servAddr.sin_port = htons(port);              /* Local port */
	if (bind(servSock, (struct sockaddr *)&servAddr, sizeof(servAddr)) < 0){
		printf("callback::createServerSocket(): ERROR: Bind on port %d failed!\n", port);
	}
	if (listen(servSock, MAXPENDING) < 0){
		printf("callback::createServerSocket(): ERROR: Listen on port %d failed!\n", port);
	}
	return servSock;

}

// Here we establish socket connectivity with another endpoint/program on 'port' argument
void clientSendSocket(int port, char *buffer)
{
	int sockfd = 0;
	struct sockaddr_in servAddr;
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		printf("callback::clientSocket():ERROR : Could not create socket \n");
	}
	memset(&servAddr, 0, sizeof(servAddr));
	servAddr.sin_family = AF_INET;
	servAddr.sin_port = htons(port);
	servAddr.sin_addr.s_addr = inet_addr(HOST);
	if (connect(sockfd, (struct sockaddr *)&servAddr, sizeof(servAddr)) < 0)
	{
		printf("callback::clientSocket():ERROR : Connect Failed on Port: %d\n", port);
	}
	else
	{
		send(sockfd, buffer, strlen(buffer), 0);
		printf("callback::clientSendSocket(): Data sent Successfully on Port: %d\n", port);
	}
	close(sockfd);
}
void callbackFunction(ParseClient client, int error, const char *buffer) 
/*void callbackFunction(ParseClient client, int error, int httpStatus, const char* httpResponseBody) */{
	/*if (error == 0 && httpResponseBody != NULL) */ 	
	if (error == 0 && buffer != NULL){
		//printf("callback:callback()::Received Push Data: '%s'\n", buffer);
	}
	strcpy(copied_string, buffer);
	printf("Beginning of callback()\n");
	clientSendSocket(PORT_CALLBACK, copied_string);
	//printf("buffer: '%s'\n", copied_string);

}

// This function pushes data onto the Parse Application in cloud. It is invoked by updateIntensity().
void *threadPushNotifications()
{
	pthread_detach(pthread_self());
	//IOT_RPI_SCL ParseClient client = parseInitialize("kayWALfBm6h1SQdANXoZtTZqA0N9sZsB7cwUUVod", "7Nw0R9LTDXR7lRhmPsArePQMralFW8Yt7DL2zWTS");
	//Group 14 SCL ParseClient client = parseInitialize("TSexah1prtbhpF6w4dellQ2XYWyk2bqcljOiElrN", "xLnvnzcTMO1w9MwuFNBTO6hLjOtnKmZn4iz4SBnu");
	//Group 14 surveillance
	ParseClient client = parseInitialize("ajdBM8hNORYRg6VjxOnV1eZCCghujg7m12uKFzyI", "NVqqhuoWKdxJS6bNI5lPvignPXZahOlc8Ylr9zDc");
	char *installationId = parseGetInstallationId(client);

	parseSetInstallationId(client, dataUUID);
	printf("callback::threadPushNotifications():New Installation ID set to : %s\n", installationId);
	printf("callback::threadPushNotifications():Installation ID is : %s\n", installationId);	
	parseSetPushCallback(client, callbackFunction);
	parseStartPushService(client);
	parseRunPushLoop(client);
	//printf("Somewhere in threadPushNotifications()\n");
	
	
}


//@TODO: IMPLEMENT MAIN FUNCTION

int main() {
	//char str[4];
	pthread_t threadPush;
	pthread_mutex_init(&lock, NULL);

	int ctrlCameraSocket = createServerSocket(PORT_CALLBACK);
	pthread_mutex_lock(&lock);
	pthread_mutex_unlock(&lock);

	pthread_create(&threadPush, NULL, threadPushNotifications, NULL);
	
	while(1){
		//clientSendSocket(PORT_CALLBACK, copied_string);
	}	

	return 0;
}
