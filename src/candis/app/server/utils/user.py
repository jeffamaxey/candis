class MailMessage():
    
    @classmethod
    def forgot_password_body(cls, url, reset_token, time):
        url = f'{url}?reset_token={reset_token}'
        return f'<h2>Reset token is: </h2><a href={url}>{reset_token}</a><h3>Link is valid for {time}.</h3>'
