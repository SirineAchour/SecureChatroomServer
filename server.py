import configparser
import base64
import sys, socket, select
from Crypto.Cipher import AES
import hashlib
import os
import signal
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography import utils
from cryptography.hazmat.primitives import serialization
import datetime
import time
from cryptography.hazmat.primitives.asymmetric import padding


from ldapservice import LdapService
from user import User

def sigint_handler(signum, frame):
    print("\033[91m"+"\nServer shutdown !!"+"\033[0m")
    print("\n\n")
    sys.exit()  

signal.signal(signal.SIGINT, sigint_handler)


config = configparser.RawConfigParser()
config.read(r'chat.conf')

HOST = config.get('config', 'HOST')
PORT = int(config.get('config', 'PORT'))
PASSWORD = config.get('config', 'PASSWORD')
VIEW = str(config.get('config', 'VIEW'))
SOCKET_LIST = []
CONNECTED_USERS=[]

BUFFER_SIZE = 8192
clients = []

client_sockets = {}

def get_ca_pk() :
    pem_ca_cert = open('cert.pem','rb').read()
    
    ca_cert = x509.load_pem_x509_certificate(pem_ca_cert, default_backend())
    ca_pk = ca_cert.public_key()
    return ca_pk

verify_cert = True
client_pk = {}

def gen_certificate(ind) : 
    one_day = datetime.timedelta(1, 0, 0)
    pem_ca_cert = open('cert.pem','rb').read()
    ca_cert = x509.load_pem_x509_certificate(pem_ca_cert, default_backend())
    pem_ca_key = open('key.pem' , 'rb').read()
    ca_key = serialization.load_pem_private_key(pem_ca_key, password = None,backend = default_backend())
    pem_req_data = open("clientcsr" + str(ind) + ".pem",'rb').read()
    csr = x509.load_pem_x509_csr(pem_req_data, default_backend())
    csr_public_key = csr.public_key()
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(csr.subject)
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.not_valid_before(datetime.datetime.today() - one_day)
    builder = builder.not_valid_after(datetime.datetime(2023, 8, 2))
    builder = builder.serial_number(utils.int_from_bytes(os.urandom(20), "big") >> 1)
    builder = builder.public_key(csr_public_key)
    print("extensions")
    for ext in csr.extensions :
        builder = builder.add_extension(ext.value , ext.critical)
    print("signing the cert")
    certificate = builder.sign(
        private_key=ca_key, algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    print("writing the cert")
    certificatepem = "certificate" + str(ind) + ".pem"
    with open(certificatepem, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))
    print(str(certificatepem))
    print("ALMOST DONE WIT CERT GEN")
    return certificate.public_bytes(serialization.Encoding.PEM),csr_public_key,ca_key

class myclient:
    def __init__(self, ind,login,pk,crt):
        self.login = login
        self.ind = ind
        self.pk = pk
        self.crt = crt

def send_file(sock , file) :
    print("gonna send file")
    f = open(file, 'rb') 
    print("opened file successfully")
    l = f.read(8192)
    print("read file contents :")
    print(str(l))

    print("sock ?")
    print(sock)
    sock.sendall(l.encode('utf-8'))
    print("done sending all ")
    f.close()
    print("closed file")
    sock.recv(1)
    print("done sending file")

def send_msg(sock,msg) : 
    data = msg.encode('utf-8')
    sock.sendall(data)
    sock.recv(1)

def recv_msg(sock) : 
    print("server waiting for msg")
    print("sock = "+str(sock))
    data = sock.recv(8192)
    print("got it : "+str(data))
    print(data.decode("utf-8"))
    print(len(data.decode("utf-8")))
    print("sock remote @ : "+str(sock.getpeername()))
    print("sock name : "+str(sock.getsockname()))
    print("sock tyoe : "+str(sock.type))
    sock.sendall('1'.encode('utf-8'))
    print("sent 1 to all")
    return data.decode("utf-8")

def write_file(sock,data,file) :
    filename=str(file)
        
    with open(filename,'wb') as f : 
        f.write(data)

def encrypt(public_key,msg):
    ciphertext = public_key.encrypt(
    msg,
    padding.OAEP(
         mgf=padding.MGF1(algorithm=hashes.SHA256()),
         algorithm=hashes.SHA256(),
         label=None
    )
    )
    return ciphertext

def decrypt (public_key,msg):
    data = public_key.decrypt(
    msg,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    )

    return data

def register_client(data,_id,sock) :

    write_file(sock,data,'clientcsr' + str(_id) + '.pem')
    print("done writing file")
    certificate,public_key,ca_key = gen_certificate(_id)
    print("done generating certif")

    send_file(sock,"certificate" + str(_id) + ".pem")
    print("done sending certif")
    send_file(sock,"cert.pem")
    print("done sending cert.pem")
    login = recv_msg(sock)
    password = recv_msg(sock)
    email = recv_msg(sock)
    carte = recv_msg(sock)
    #here
    print("about to load ldap service")
    ldapServ=LdapService()
    print("got ldap service")
    print(str(ldapServ))
    user=User(login,login,login,email,password,carte,certificate)
    print("loaded user object")
    print("adding user")
    ldapServ.add_user(user)
    print("done user added")
    client_pk[login] = public_key
    print("set publilc key ")
    newclient = myclient(_id,login,public_key,certificate)
    print("!!!!!!!!!!!!!!created new client")
    clients.append(newclient)
    send_msg(sock,'YES')
    return login,password

def send_available_clients(sock,_id):
    for client in clients :
        if client.ind == _id :
            continue
        send_msg(sock,client.login)
    send_msg(sock,'abc')

def auth_client(sock,_id) : 

    login = recv_msg(sock)
    password = recv_msg(sock)
    ldapServ = LdapService()
    print("login :")
    print(str(login))
    user=ldapServ.search_user(login)



    if login == user.uid[0] and password == user.password[0]  : 

        client_sockets[login] = sock
        send_msg(sock,'done')
        send_available_clients(sock,_id)

    else :
        send_msg(sock,'credentials non existent')
        recv_msg(sock)
        auth_client(sock,_id,reglogin,regpassword)

def transmit_msg(_id,reciever,sock) : 
    pem_ca_key = open('key.pem' , 'rb').read()
    ca_key = serialization.load_pem_private_key(pem_ca_key, password = None,backend = default_backend())
    msg= recv_msg(sock)

    msg = decrypt(ca_key,msg)
    msg = encrypt(client_pk[reciever],msg)
    send_msg(client_sockets[reciever],msg)
  
def chat_server():
    LdapService.created_group = False
    ind = "100"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    SOCKET_LIST.append(server_socket)

    print("neuron server started on port " + str(PORT))

    while 1:
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)

        for sock in ready_to_read:
            print("in for loop")
            if sock == server_socket:
                print("server socket")
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                send_msg(sockfd,ind)
                ind = str(int(ind) + 1 )
                print("user"+ str(addr)+"connected")
            else:
                print("in else")
                try:
                    print("gonna try to receive msg")
                    data = recv_msg(sock)
                    print("got message containing data")
                    print("data :")
                    print(str(data))
                    if data:
                        _id = data [:3]
                        if data[3:6] == 'csr' :
                            print("in new client")
                            reglogin,regpassword = register_client(data[6:],_id,sock)
                            print("done with new client")
                        elif data[3:6] == 'aut' :
                            print("about to log an old client" )
                            login,password = auth_client(sock,_id)
                            print(login + " + " +password)
                            print("done with login")
                        elif data[3:6] == 'msg' : 
                            print("gonna wait for msg")
                            reciever = recv_msg(sock)
                            print("gonna transmit msg")
                            transmit_msg(_id,reciever,sock)
                            print("done transmitting l msg")
                        elif VIEW == '1':
                            print("in last elif")
                            print(clients[int(_id)] + ' : ' + data )
                    else:
                        print("in big else gonna remove sock")
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)
                except:
                    print("something went wrong bye")
                    #continue
                    sys.exit()

    server_socket.close()

def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:

        if socket != server_socket and socket != sock :
            try :
                socket.sendall(message.encode('utf-8'))
            except :

                socket.close()

                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)
os.system("clear")
print("""
    *********************************
     CHAT ROOM SERVER STARTING .....               
        *********************************
"""
)

if __name__ == "__main__":
    sys.exit(chat_server())

