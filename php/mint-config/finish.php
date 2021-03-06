<?php

    if (!file_exists($mint_config) and empty($_GET['result'])) {
        BrowserRedirect('/mint-config/1');
    }

    if ($_GET['result'] === "0") { ?>
        <h3 class="success">Configuration Successfully Encrypted</h3>
        <div id="guide">
            <section>
                <p>Your configuration is encrypted and stored in a secure location that gets destroyed when you remove or update LooPyGen.</p>
                <p>If you forget your passphrase for any reason, or need to change the private key to another wallet, simply remake your config again with a new passphrase.</p>
            </section>
        </div>
        <div class="nav"><a href="/">BACK TO HOME</a></div>
        <div class="nav"><a href="/mint-config/1">REMAKE CONFIG</a></div>
    <?php } else {
        if (file_exists($mint_config)) { unlink($mint_config); } ?>
        <h3 class="error">Configuration Not Encrypted</h3>
        <?php if ($_GET['result'] === "100") { ?>
            <h3 class="warning">Your passphrases did not match.</h3>
        <?php } ?>
        <div id="guide">
            <section>
                <p>Your configuration was not stored.</p>
                <p>Please try again.</p>
            </section>
        </div>
        <div class="nav"><a href="/mint-config/1">RETRY CONFIG</a></div>
    <?php }

?>