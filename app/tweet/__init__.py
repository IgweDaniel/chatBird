
tweet_serializer = TweetSchema()
tweets_serializer = TweetSchema(many=True)


@user.route('/statuses')
def get_status():
    u = Tweet.query.all()[2]
    tweet = tweet_serializer.dump(u)
    print(tweet)
    return jsonify({'data': tweet})
