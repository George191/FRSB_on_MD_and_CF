import pandas as pd
import numpy as np
import tensorflow as tf
tf.device('/gpu:0')
ratings_df = pd.read_csv('D:/PythonProjects/FRSB on_MD_and_CF/ml-latest-small/ratings.csv')
movies_df = pd.read_csv('D:/PythonProjects/FRSB on_MD_and_CF/ml-latest-small/movies.csv')

print(ratings_df.tail())
print(movies_df.tail())
movies_df['movieRow'] = movies_df.index
print(movies_df.tail())
movies_df = movies_df[['movieRow', 'movieId', 'title']]
movies_df.to_csv('D:/PythonProjects/FRSB on_MD_and_CF/moviesProcessed.csv', index=False, header=True, encoding='utf-8')
print(movies_df.tail())
ratings_df = pd.merge(ratings_df, movies_df, on='movieId')
print(ratings_df.head())
ratings_df = ratings_df[['userId', 'movieRow', 'rating']]
ratings_df.to_csv('D:/PythonProjects/FRSB on_MD_and_CF/ratingsProcessed.csv', index = False, header=True, encoding='utf-8')
print(ratings_df.head())

userNo = ratings_df['userId'].max()+1
movieNo = ratings_df['movieRow'].max()+1
print(userNo)
print(movieNo)
rating = np.zeros((movieNo, userNo))

flag = 0
ratings_df_length = np.shape(ratings_df)[0]

for index, row in ratings_df.iterrows():
    rating[int(row['movieRow']), int(row['userId'])] = row['rating']
    flag += 1
    if flag % 5000 == 0:
        print('processed %d, %d left' % (flag, ratings_df_length-flag))

record = rating>0
print(record)
record = np.array(record, dtype=int)
print(record)

def normalizeRatings(rating, record):
    m, n = rating.shape
    rating_mean = np.zeros((m, 1))
    rating_norm = np.zeros((m, n))
    for i in range(m):
        idx = record[i, :] !=0
        rating_mean[i] = np.mean(rating[i, idx])
        rating_norm[i, idx] -= rating_mean[i]
    return rating_norm, rating_mean

rating_norm, rating_mean = normalizeRatings(rating, record)
rating_norm = np.nan_to_num(rating_norm)
print(rating_norm)
rating_mean = np.nan_to_num(rating_mean)
print(rating_mean)

num_features = 10
X_parameters = tf.Variable(tf.random_normal([movieNo, num_features], stddev=0.35))
Theta_paramters = tf.Variable(tf.random_normal([userNo, num_features], stddev=0.35))
loss = 1/2 * tf.reduce_sum(((tf.matmul(X_parameters, Theta_paramters, transpose_b=True) - rating_norm)*record)**2) + \
    1/2 * (tf.reduce_sum(X_parameters**2) + tf.reduce_sum(Theta_paramters**2))
optimizer = tf.train.AdamOptimizer()
train = optimizer.minimize(loss)

tf.summary.scalar('loss', loss)
summaryMerged = tf.summary.merge_all()
filename = 'D:/PythonProjects/FRSB on_MD_and_CF/movie_tensorboard'
writer = tf.summary.FileWriter(filename)

sess = tf.Session()
init = tf.global_variables_initializer()
sess.run(init)

penalty = movieNo*userNo

for i in range(3000):
    l, _, movie_summary = sess.run([loss, train, summaryMerged])
    if i%100 == 0:
        Current_X_parameters, Current_Theta_parameters = sess.run([X_parameters, Theta_paramters])
        predicts = np.dot(Current_X_parameters,Current_Theta_parameters.T) + rating_mean
        errors = np.mean((predicts - rating)**2)
        print('step:', i, ' train loss:%.5f' % (l/penalty), ' test loss:%.5f' % errors)
    writer.add_summary(movie_summary, i)

Current_X_parameters, Current_Theta_parameters = sess.run([X_parameters, Theta_paramters])
predicts = np.dot(Current_X_parameters,Current_Theta_parameters.T) + rating_mean
errors = np.mean((predicts - rating)**2)

print(errors)

user_id = input('您要向哪位用户进行推荐？请输入用户编号：')

sortedResult = predicts[:, int(user_id)].argsort()[::-1]

idx = 0
print('为该用户推荐的评分最高的20部电影是：'.center(80, '='))
for i in sortedResult:
    print('评分：%.2f, 电影名：%s' % (predicts[i, int(user_id)], movies_df.iloc[i]['title']))
    idx += 1
    if idx == 20: 
        break