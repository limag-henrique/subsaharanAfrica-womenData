# Saúde da Mulher na África Subsaariana

*Feito por: Henrique Gusmão, Felipe Franco, Izabella Correia, Alice Silva \- **TZ1***

## Descrição do dataset

Este dataset filtrado abrange visões integradas sobre a saúde \+ condições de vida da mulher na África Subsaariana. Oriundo do programa DHS (*Demographic and Health Surveys,* do Governo Estadunidense/Fundação Gates), ele contém mais de 4,5 milhões de registros interligados, de 37 países/nações. Com a informação de 407,6 mil mulheres, 877,4 mil nascimentos, é possível analisar a saúde pré e pós natal, pobreza, desigualdades territoriais, e violência de gênero.

## Inovação social

Podemos investigar onde, como e para quem as desigualdades se acumulam para **1,2 bilhão de habitantes:**

* Correlação rural-riqueza-escolaridade \-distância dos serviços, para **orientar recursos** para a saúde obstétrica;  
* **Pobreza multidimensional** e saúde;   
* **Planejamento familiar** e autonomia feminina;   
* Desigualdades urbano-rurais;   
* **Mapas de vulnerabilidade**;   
* Modelos preditivos para **direcionar** maior atenção pelas agências de apoio humanitário;   
* **Descobrir** políticas públicas bem-sucedidas.

## Entidades

* **País**(código, nome) *{37 instâncias}*  
* **Pessoa**(ID, FK\_Pais, FK\_domicilio, Relacao\_chefe\_domicilio, escolaridade, estado\_civil, idade, etnia) *{1.884.683*  *instâncias*}   
* **Mulher**(ID\_Pessoa, Religião, IdadePrimeiraGestação, Total\_Gestações, Conhecimento\_Método) *{407,6 mil instâncias}*  
* **Parceiro**(ID\_Pessoa, IdadePrimeiroFilho, Total\_Filhos) *{236.070 instâncias}*  
* **Levantamento**(ID, país\_codigo, Fase\_DHS) *{108 instâncias}*  
* **Metodo\_anticoncepcional**(ID\_Antic, nome, classificação) *{19 instâncias}*  
* **Entrevista**(ID\_entr, data, FK\_Levantamento) *{407.600 instâncias}*  
* **Filho**(entidade fraca) (ID\_Filho, peso, altura, FK\_Nascimento, sexo, esta\_vivo, peso\_ao\_nascer, nasceu\_vivo, idade\_morte\_meses, mora\_com\_mae, duracao\_aleitamento, Diarreia\_ultimas\_2\_sem, Cartao\_vacina\_visto) {*282.641 instâncias*}  
* **Domicílio**(ID\_Dom , Região, Rural\_ou\_Urbano, FK\_País, n\_homens, n\_mulheres, n\_membros, fonte\_agua, tem\_eletricidade, tem\_carro, FK\_pessoa\_chefe, Lavagem\_Maos\_Adequadas, Indice\_Riqueza, pai\_mora, mae\_mora) {*385.457 instâncias*}  
* **Nascimento/Gestação**(ano, mês, assistencia\_parto, local\_nascimento, FK\_Filho, FK\_Mãe, n\_consultas\_pre\_natais, Intervalo\_Ultimo\_Nasc, Intervalo\_Apos\_Nasc, Cesaria) *{877.412 instâncias}*  
* **Vacina\_Remedio**(id\_vacina, nome) \- {*8 instâncias*}  
* **Servico\_publico**(ID\_Serv, Rural\_ou\_Urbano, Data\_Fim\_Visita, Fonte\_Agua, Instalacao\_Sanitaria) *{5.154 instâncias}*

Relacionamento

* Filho \- recebe \- Vacina\_Remedio (N:M) \- *1.174.167*   
* Domicílio \- pertence a \- País (N:1) \- *385.457*  
* Entrevista/Mulher \- pertence a \- Levantamento (N:1) \- *407.600*  
* Levantamento/Mulher \- realizado em \- País (N:1) \- *108*  
* Mulher \- conhece \- Metodo\_anticoncepcional (N:M) \- *2.409.894*  
* Servico\_Publico \- realizado \- País (N:1) \- *5.154*  
* Mulher \- já usou \- Metodo\_anticoncepcional (N:M) \- *16.978*  
* Mulher \- usa atualmente \- Metodo\_anticoncepcional (N:M) \- *101.972*  
* Mulher \- possui \- Nascimento/Gestação (1:N) \-  *877.412*  
* Mulher \- relaciona-se com \- Parceiro (N:M) \- *109.174*  
* Mulher \- reside em \- Domicílio (N:1) \- 401.740  
* Nascimento/Gestação \- resulta em \- Filho (1:N) \- 282.641