import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging

# Function to get a database connection.
# This function connects to database with the name `database.db`
connection_count = 0


def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID

def get_post(post_id):
    global connection_count
    connection = get_db_connection()
    connection_count += 1
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    connection_count -= 1
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application


@app.route('/')
def index():
    global connection_count
    connection = get_db_connection()
    connection_count += 1
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    connection_count -= 1
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.exception('The post with post_id {} is not found.'.format(str(post_id)))
        return render_template('404.html'), 404
    else:
        app.logger.info('Article {} retrieved!'.format(post['title']))
        return render_template('post.html', post=post)

# Define the About Us page


@app.route('/about')
def about():    
    app.logger.info('About Us page request successful.')
    return render_template('about.html')

# Define the post creation functionality


@app.route('/create', methods=('GET', 'POST'))
def create():
    global connection_count
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection_count += 1
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()
            connection_count -= 1
            
            app.logger.info('A new article with title {} is created.'.format(title))
            
            return redirect(url_for('index'))

    return render_template('create.html')

# Returns the health of TechTrends application

## Gets the health of the system
@app.route('/healthz')
def healthcheck():  
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    app.logger.info('healthz request successful.')
    app.logger.debug('DEBUG message')
    return response


## Gets the metrics of the system
@app.route('/metrics')
def metrics():
    global connection_count
    connection = get_db_connection()
    connection_count += 1          
    try:          
        posts_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        connection.close()
        connection_count -= 1
    except sqlite3.Error as ex:
        app.logger.exception("Error in executing query")
        app.logger.exception(' '.join(ex.args))
        
    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": connection_count, "post_count": posts_count}),
            status=200,
            mimetype='application/json'
    )
    
    app.logger.info('Metrics request successful.')
    return response


# start the application on port 3111
if __name__ == "__main__":
    # set logger to handle STDOUT and STDERR 
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    handlers = [stdout_handler, stderr_handler]    
    log_format = '%(levelname)s:%(module)s:%(asctime)s, %(message)s'           
    logging.basicConfig(format=log_format, level=logging.DEBUG, handlers=handlers)
            
    app.run(host='0.0.0.0', port='3111')
