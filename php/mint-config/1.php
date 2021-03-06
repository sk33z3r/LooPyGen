<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Getting Your Private Key</h3>
        <div id="guide">
            <section>
                <p>STEP 01 - Export your account info to get your Private Key.</p>
                <ol>
                    <li>Login to the <a href="https://loopring.io/#" target="_blank">Loopring Wallet</a></li>
                    <li>Go to <b>L2 Wallet -> Security -> Export Account</b></p></li>
                </ol>
            </section>
        </div>
        <form method="post" action="/mint-config/1">
            <h3>Minter Info</h3>
            <section id="artist">
                <div data-tooltip="Minter Address: The L2 wallet address or ENS or Account ID of the minter"><input required type="text" class="form wide" id="minter" name="minter" placeholder="Minter Address [Wallet Address, ENS, or Account ID]" /></div>
                <div data-tooltip="Minter Private Key: The Loopring private key of the minter [DO NOT SHARE THIS INFO WITH ANYONE]"><input required type="password" class="form wide" id="private_key" name="private_key" placeholder="Minter Private Key" /></div>
                <div data-tooltip="Config Passphrase: A passphrase to encrypt your private key with [DO NOT SHARE THIS INFO WITH ANYONE]"><input required type="password" class="form wide" id="secret" name="secret" placeholder="Config Passphrase" /></div>
                <div data-tooltip="Confirm Passphrase: Re-type the passphrase you previously entered [DO NOT SHARE THIS INFO WITH ANYONE]"><input required type="password" class="form wide" id="pass_confirm" name="pass_confirm" placeholder="Confirm Passphrase" onpaste="return false;" /></div>
                <div data-tooltip="Default Royalty Percentage: Percentage of the price of a sale that will go to the Royalty Address (LooPyGen generated collections override this percentage)">
                    <input required type="number" class="form wide" id="royalty_percentage" min="0" max="10" name="royalty_percentage" placeholder="Default Royalty Percentage: 0-10" />
                </div>
                <div class="row">
                    <div data-tooltip="NFT Type: EIP-1155 (recommended) or EIP-721">
                        <select required class="form med" id="nft_type" name="nft_type">
                            <option value="0">EIP-1155</option>
                            <option value="1">EIP-721</option>
                        </select>
                    </div>
                    <div data-tooltip="Fee Token: The token to be used to pay protocol fees">
                        <select required class="form med" id="fee_token" name="fee_token">
                            <option value="1">LRC</option>
                            <option value="0">ETH</option>
                        </select>
                    </div>
                </div>
            </section>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="FINISH" />
        </form>
    <?php } else {
        $minter = $_POST['minter'];
        $private_key = $_POST['private_key'];
        $secret = base64_encode($_POST['secret']);
        $pass_confirm = base64_encode($_POST['pass_confirm']);
        $royalty_percentage = $_POST['royalty_percentage'];
        $nft_type = $_POST['nft_type'];
        $fee_token = $_POST['fee_token'];

        if ($secret !== $pass_confirm) {
            $code = "100";
        } else {
            $config_data = array("minter"=>$minter,
                                 "private_key"=>$private_key,
                                 "royalty_percentage"=>(int)$royalty_percentage,
                                 "nft_type"=>(int)$nft_type,
                                 "fee_token"=>(int)$fee_token);

            $config_json = json_encode($config_data, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
            file_put_contents($mint_config, $config_json);

            # encrypt the config file
            $command = "encrypt --mint --secret ${secret}";
            exec($command, $output, $code);
        }

        Redirect("/mint-config/finish?result=${code}", false);
    }

?>