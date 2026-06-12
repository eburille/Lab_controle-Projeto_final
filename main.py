import sys
import multiprocessing as mp
from multiprocessing.connection import Connection
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

# Tenta importar o seu módulo de controle
try:
    from controlador import run
except ImportError:
    # Fallback apenas para não travar o script caso testado isoladamente
    def run(pipe): pass

class DashControl(QWidget):
    def __init__(self, pipe_conn: Connection):
        super().__init__()
        self.pipe = pipe_conn
        
        # Estado inicial do controle: 0 = Velocidade, 1 = Posição
        self.modo_controle = 0 
        
        self.initUI()
        
        # Timer para ler a telemetria vinda do loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.receber_telemetria)
        self.timer.start(50)

    def initUI(self):
        # Estilo Dark Mode com diferenciação para o botão de modo e presets
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #E0E0E0; }
            QFrame { border: 2px solid #333; border-radius: 10px; background-color: #1E1E1E; }
            QLabel { border: none; }
            QLineEdit { background-color: #2D2D2D; border: 1px solid #444; padding: 5px; color: #00FFCC; }
            QPushButton { background-color: #007BFF; border-radius: 5px; padding: 10px; font-weight: bold; color: white; }
            QPushButton:hover { background-color: #0056b3; }
        """)

        main_layout = QVBoxLayout()

        # --- BOTÃO DE ALTERNANCIA DE MODO ---
        self.btn_modo = QPushButton("MODO: CONTROLE DE VELOCIDADE")
        self.btn_modo.setFont(QFont('Arial', 11, QFont.Bold))
        self.btn_modo.setStyleSheet("background-color: #00B4D8; color: #121212;")
        self.btn_modo.clicked.connect(self.alternar_modo_controle)
        main_layout.addWidget(self.btn_modo)

        # --- SEÇÃO DE TELEMETRIA ---
        telemetria_layout = QHBoxLayout()
        
        self.frame_pos = QFrame()
        l_pos = QVBoxLayout(self.frame_pos)
        l_pos.addWidget(QLabel("POSIÇÃO ATUAL (rad)"), alignment=Qt.AlignCenter)
        self.val_pos = QLabel("0.00")
        self.val_pos.setFont(QFont('Courier New', 30, QFont.Bold))
        self.val_pos.setStyleSheet("color: #00FFCC;")
        l_pos.addWidget(self.val_pos, alignment=Qt.AlignCenter)
        
        self.frame_vel = QFrame()
        l_vel = QVBoxLayout(self.frame_vel)
        l_vel.addWidget(QLabel("VELOCIDADE ATUAL (m rad/s)"), alignment=Qt.AlignCenter)
        self.val_vel = QLabel("0.00")
        self.val_vel.setFont(QFont('Courier New', 30, QFont.Bold))
        self.val_vel.setStyleSheet("color: #FFCC00;")
        l_vel.addWidget(self.val_vel, alignment=Qt.AlignCenter)

        telemetria_layout.addWidget(self.frame_pos)
        telemetria_layout.addWidget(self.frame_vel)
        main_layout.addLayout(telemetria_layout)

        # --- SEÇÃO DE PRESETS / REFERÊNCIAS PREDEFINIDAS (NOVO) ---
        presets_layout = QVBoxLayout()
        presets_layout.addWidget(QLabel("REFERÊNCIAS PREDEFINIDAS (POSIÇÃO)"))
        
        presets_row = QHBoxLayout()
        
        self.btn_preset_628 = QPushButton("Posição: 360°")
        self.btn_preset_628.setStyleSheet("background-color: #28A745; font-weight: bold;") # Verde
        self.btn_preset_628.clicked.connect(lambda: self.aplicar_preset_posicao(6.28))
        
        self.btn_preset_0 = QPushButton("Posição: 0.00°")
        self.btn_preset_0.setStyleSheet("background-color: #DC3545; font-weight: bold;")  # Vermelho
        self.btn_preset_0.clicked.connect(lambda: self.aplicar_preset_posicao(0.0))
        
        presets_row.addWidget(self.btn_preset_628)
        presets_row.addWidget(self.btn_preset_0)
        presets_layout.addLayout(presets_row)
        main_layout.addLayout(presets_layout)

        # --- SEÇÃO DE COMANDO (INPUTS MANUAIS) ---
        cmd_layout = QVBoxLayout()
        cmd_layout.addWidget(QLabel("AJUSTAR REFERÊNCIA DO SISTEMA MANUALMENTE"))
        
        input_row = QHBoxLayout()
        self.input_pos = QLineEdit()
        self.input_pos.setPlaceholderText("Ref Posição")
        self.input_vel = QLineEdit()
        self.input_vel.setPlaceholderText("Ref Velocidade")
        input_row.addWidget(self.input_pos)
        input_row.addWidget(self.input_vel)
        
        self.btn_enviar = QPushButton("ENVIAR COMANDO")
        self.btn_enviar.clicked.connect(self.enviar_comando)
        
        cmd_layout.addLayout(input_row)
        cmd_layout.addWidget(self.btn_enviar)
        main_layout.addLayout(cmd_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('Dashboard de Controle Motor')
        self.resize(550, 520) # Redimensionado ligeiramente para comportar os novos botões

    def aplicar_preset_posicao(self, valor_pos: float):
        """ Preenche o campo de texto de posição com o preset escolhido e envia imediatamente """
        self.input_pos.setText(str(valor_pos))
        # Força o modo de controle para Posição (1) se o usuário usar o preset de posição
        if self.modo_controle == 0:
            self.alternar_modo_controle()
        else:
            self.enviar_comando()

    def alternar_modo_controle(self):
        """ Alterna a variável de estado e atualiza o visual do botão """
        if self.modo_controle == 0:
            self.modo_controle = 1
            self.btn_modo.setText("MODO: CONTROLE DE POSIÇÃO")
            self.btn_modo.setStyleSheet("background-color: #9D4EDD; color: white;")
        else:
            self.modo_controle = 0
            self.btn_modo.setText("MODO: CONTROLE DE VELOCIDADE")
            self.btn_modo.setStyleSheet("background-color: #00B4D8; color: #121212;")
        
        self.enviar_comando()

    def enviar_comando(self):
        try:
            nova_ref = {
                "modo": self.modo_controle,
                "ref_pos": float(self.input_pos.text() if self.input_pos.text() else 0.0),
                "ref_vel": float(self.input_vel.text() if self.input_vel.text() else 0.0)
            }
            self.pipe.send(nova_ref)
            print(f"[GUI] Referências enviadas: {nova_ref}")
        except ValueError:
            print("[GUI] Erro: Digite números válidos!")

    def receber_telemetria(self):
        while self.pipe.poll():
            dados = self.pipe.recv()
            if "posicao" in dados:
                self.val_pos.setText(f"{dados['posicao']:.2f}")
                self.val_vel.setText(f"{(dados['velocidade']*1000):.2f}")

def rodar_gui(pipe_conn):
    app = QApplication(sys.argv)
    ex = DashControl(pipe_conn)
    ex.show()
    sys.exit(app.exec_())

# --- ORQUESTRAÇÃO DE INICIALIZAÇÃO ---
if __name__ == '__main__':
    # Cria o Pipe bidirecional seguro para troca de dados em memória
    conn_gui, conn_control = mp.Pipe(duplex=True)
    
    # Cria e inicializa o processo secundário para a matemática do controle
    p_control = mp.Process(target=run, args=(conn_control,))
    p_control.daemon = True 
    p_control.start()

    # Inicia a GUI na thread principal do sistema gráfico local
    rodar_gui(conn_gui)