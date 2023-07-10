# REAL TIME ASSET MANAGER API

# !!! Under Construction !!!

### Welcome to the asset manager.

## Building the asset manager.

To create the Postgres DB run the app first run: 
> >docker compose up

To make sure the migrations are updated:
> >python manage.py makemigrations ativos

To export them to the db:
> > python manage.py migrate ativos


### The api manages three classes: 
> #### ações, fiis, etfs_br, stocks, reits, etfs_us, cryptos

## Routes
### Getting all wallet assets:
> >**[GET] /ativo/**

### Getting all assets of a specific class:
> >**[GET] /ativo/{classe}**

### Posting or updating an asset (except cryptos):
This route is to **create** a new asset or **update** an existing one. 

Ps.: For **cryptos** the request body is different.
> >**[POST] /ativo/{classe}**
> >
> >{
> > "nome": "PETR4",
> > "preço_un": 24.00,
> > "quantidade": 10,
> > "dividendos": false
> > }

Where:
- 'nome' is the asset **ticker** like: GOOGL, AAPL, BTC, BBSA3 etc.
- 'preço_un' is the price of one unit of that asset.
- 'quantidade' is the amount purchased.
- 'dividendos' is the origin of the money. Is it reinvestment or not?

### Posting or updating a crypto purchase:
> >**[POST] /ativo/{classe}**
> >
> >{
> > "nome": "PETR4",
> > "preço_un": 24.00,
> > "quantidade": 10,
> > "dividendos": false
> > }









