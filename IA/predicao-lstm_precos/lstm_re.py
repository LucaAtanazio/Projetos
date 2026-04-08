import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
import glob
import matplotlib.pyplot as plt
import os 
from datetime import timedelta

# 1. Configuração de Hardware
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Treinando na: {device}")

# 2. Função de Carga Robusta (Com Calendário)
def load_specific_game(search_term="7-"):
    base_path = os.path.dirname(os.path.abspath(__file__))
    all_files = glob.glob(os.path.join(base_path, "*.csv"))
    
    for file in all_files:
        if search_term.upper() in os.path.basename(file).upper():
            print(f"Arquivo encontrado: {os.path.basename(file)}")
            
            df = pd.read_csv(file, quotechar='"')
            df.columns = [c.strip() for c in df.columns]
            df = df.dropna(subset=['Final price'])
            df['DateTime'] = pd.to_datetime(df['DateTime'])
            
            df['Month'] = df['DateTime'].dt.month
            df['Is_Promo_Month'] = df['Month'].apply(lambda x: 1 if x in [6, 7, 10, 11, 12] else 0)

            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_features = scaler.fit_transform(df[['Final price', 'Is_Promo_Month']].values)

            return scaled_features, scaler, os.path.basename(file), df
            
    return None, None, None, None

# 3. Preparação das Sequências
def create_sequences(data, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        x = data[i:(i + seq_length)]
        y = data[i + seq_length, 0] #
        ys.append(y)
    return np.array(xs), np.array(ys)


def inverse_transform_price(scaler, price_array):
    dummy = np.zeros((len(price_array), 2))
    dummy[:, 0] = price_array.flatten()
    return scaler.inverse_transform(dummy)[:, 0]

# Execução da carga
SEQ_LENGTH = 45
scaled_data, scaler, game_name, df = load_specific_game("7-")

X, y = create_sequences(scaled_data, SEQ_LENGTH)

# Split temporal (80% treino)
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Conversão e Reshape 
X_train = torch.from_numpy(X_train).float().to(device)
y_train = torch.from_numpy(y_train).float().to(device).view(-1, 1)
X_test = torch.from_numpy(X_test).float().to(device)
y_test = torch.from_numpy(y_test).float().to(device).view(-1, 1)

# 4. Arquitetura LSTM Multivariada
class PriceLSTM(nn.Module):
    def __init__(self, input_size=2, hidden_layer_size=128, output_size=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_layer_size, num_layers=2, batch_first=True)
        self.linear = nn.Linear(hidden_layer_size, output_size)

    def forward(self, input_seq):
        lstm_out, _ = self.lstm(input_seq)
        return self.linear(lstm_out[:, -1])

model = PriceLSTM(input_size=2).to(device)
loss_function = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# 5. Treinamento
epochs = 300
print(f"Iniciando treino de {game_name} com suporte a Calendário...")
for i in range(epochs):
    model.train()
    optimizer.zero_grad()
    y_pred = model(X_train)
    loss = loss_function(y_pred, y_train)
    loss.backward()
    optimizer.step()
    
    if i % 50 == 0:
        print(f'Epoch {i} | Loss: {loss.item():.6f}')

# 6. Avaliação e Gráfico
model.eval()
with torch.no_grad():
    preds = model(X_test)
    preds_unscaled = inverse_transform_price(scaler, preds.cpu().numpy())
    y_test_unscaled = inverse_transform_price(scaler, y_test.cpu().numpy())

plt.figure(figsize=(12,6))
plt.plot(y_test_unscaled, label='Preço Real (Capcom)', alpha=0.7, color='#2c3e50')
plt.plot(preds_unscaled, label='Previsão (LSTM)', linestyle='--', color='#e74c3c')
plt.title(f'Análise Temporal com Calendário: {game_name}')
plt.xlabel('Passos de Tempo (Eventos de Preço)')
plt.ylabel('Preço (R$)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

diff = np.abs(y_test_unscaled - preds_unscaled)
print(f"Erro médio em Reais: R$ {diff.mean():.2f}")
print(f"Maior erro encontrado: R$ {diff.max():.2f}")

# --- 1. EXPORTAÇÃO DO MODELO ---
model_name = f"model_{game_name.replace('.csv', '')}.pth"
torch.save(model.state_dict(), model_name)
print(f"\n Modelo exportado com sucesso: {model_name}")

# --- PREVISÃO MULTI-STEP COM CONTEXTO DE DATA ---
model.eval()
with torch.no_grad():
    future_predictions = []
    # Janela inicial com 2 features (Preço + Promo)
    current_sequence = torch.FloatTensor(scaled_data[-SEQ_LENGTH:]).to(device).view(1, SEQ_LENGTH, 2)
    last_date = df['DateTime'].iloc[-1]

    for _ in range(90):
        # 1. Prediz próximo preço
        prediction = model(current_sequence)
        future_predictions.append(prediction.item())
        
        # 2. Calcula flag do mês futuro
        last_date += timedelta(days=1)
        next_promo_flag = 1 if last_date.month in [6, 7, 10, 11, 12] else 0
        
        # 3. Input de Preço Predito + Flag do Calendário
        new_entry_scaled = scaler.transform([[prediction.item(), next_promo_flag]])[0]
        new_entry_tensor = torch.FloatTensor(new_entry_scaled).to(device).view(1, 1, 2)
        
        # 4. Atualiza a sequência de rolagem
        current_sequence = torch.cat((current_sequence[:, 1:, :], new_entry_tensor), dim=1)

    future_res = inverse_transform_price(scaler, np.array(future_predictions))
    
print("\n" + "="*35)
print(" RELATÓRIO DE CALENDÁRIO ATIVO")
print(f"Amanhã: R$ {future_res[0]:.2f}")
print(f"30 dias: R$ {future_res[29]:.2f}")
print(f"90 dias: R$ {future_res[89]:.2f}")
print("="*35)